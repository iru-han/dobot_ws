import socket
import time
import DoBotArm as Dbt
import DobotDllType as dType

# --- [1. 새로운 티칭 좌표 업데이트] ---
# 물건 집기 전 경유지 (터틀봇 상공)
PICK_READY = [122.85, 166.33, 21.06]
# 실제 물건 집기 (내려가기)
PICK_DOWN = [122.9, 170.8, -53.54]
# 물건 집은 후 경유지 (높이 들기)
PICK_HIGH = [274.79, 3.94, 109.11]
# 물건 떨어뜨리는 위치
DROP_POS = [319.46, 16.25, -66.8]

HOME_POS = [250.0, 0.0, 50.0]


def wait_for_done(api, index):
    while index > dType.GetQueuedCmdCurrentIndex(api)[0]:
        alarms = dType.GetAlarmsState(api)
        # 알람이 하나라도 있는지 체크 (리스트의 합이 0보다 크면 알람 발생)
        if any(alarms[0]):
            print(f"⚠️ [ALARM {alarms}] 감지! 해제 중...")
            dType.ClearAllAlarmsState(api)
            dType.SetQueuedCmdStartExec(api)
        dType.dSleep(100)


def dobot_mission(api, conn=None):
    print("\n--- [START] Dobot Motion Sequence ---")
    dType.SetPTPCommonParams(api, 50, 50, isQueued=1)

    # STEP 1: 집기 전 경유지로 이동
    print(">> Step 1: Moving to PICK_READY")
    idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *PICK_READY, 0, isQueued=1)[0]
    wait_for_done(api, idx)

    # STEP 2: 물건 집기 (하강)
    print(">> Step 2: Moving down to PICK_DOWN")
    idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *PICK_DOWN, 0, isQueued=1)[0]
    wait_for_done(api, idx)

    print(">> Action: Suction ON")
    dType.SetEndEffectorSuctionCup(api, True, True, isQueued=1)
    time.sleep(1)

    # STEP 3: 집은 후 경유지로 이동 (회전 및 상승)
    print(">> Step 3: Moving to PICK_HIGH")
    idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *PICK_HIGH, 0, isQueued=1)[0]
    wait_for_done(api, idx)

    # STEP 4: 물건 떨어뜨리는 위치로 이동
    print(">> Step 4: Moving to DROP_POS")
    idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *DROP_POS, 0, isQueued=1)[0]
    wait_for_done(api, idx)

    print(">> Action: Suction OFF")
    dType.SetEndEffectorSuctionCup(api, True, False, isQueued=1)
    time.sleep(1)

    # STEP 5: 홈으로 복귀
    print(">> Step 5: Returning Home")
    idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *HOME_POS, 0, isQueued=1)[0]
    wait_for_done(api, idx)

    # ✅ 나중에 소켓 연결 시 신호 전송 (conn이 있을 때만 작동)
    if conn:
        print(">> [SIGNAL] Sending 'OK' to TurtleBot.")
        conn.send("OK".encode())

    print("--- [FINISH] Sequence Completed ---\n")


def main():
    ctrlBot = Dbt.DoBotArm(HOME_POS[0], HOME_POS[1], HOME_POS[2])
    dType.SetQueuedCmdClear(ctrlBot.api)
    dType.ClearAllAlarmsState(ctrlBot.api)

    # 🏠 영점 잡기 (알람 방지를 위해 필수!)
    print("🏠 Homing... (로봇의 영점을 잡습니다)")
    idx = dType.SetHOMECmd(ctrlBot.api, 0, isQueued=1)[0]
    dType.SetQueuedCmdStartExec(ctrlBot.api)
    wait_for_done(ctrlBot.api, idx)

    # --- [테스트 모드: 소켓 없이 바로 실행] ---
    """
    print("\n📢 소켓 신호 없이 바로 동작 테스트를 시작합니다.")
    dobot_mission(ctrlBot.api)
    """

    # --- [서버 모드: 나중에 사용할 때 아래 주석을 해제하세요] ---
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(1)
    print("[SERVER] Waiting for TurtleBot 'ARRIVED'...")
    try:
        while True:
            conn, addr = server.accept()
            data = conn.recv(1024).decode()
            if data == "ARRIVED":
                dobot_mission(ctrlBot.api, conn)
            conn.close()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()


if __name__ == "__main__":
    main()