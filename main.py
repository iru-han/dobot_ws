import socket
import time
import DoBotArm as Dbt
import DobotDllType as dType

# --- [사용자 지정 티칭 좌표] ---
PICK_POS = [264.38, -2.81, -18.6]  # 1. 물건 집는 위치
PICK_HIGH = [271.37, -15.44, 107.66]  # 2. 집은 후 높이 든 위치 (경유지 1)
PLACE_READY = [221.06, 175.6, 104.68]  # 3. 놓기 전 터틀봇 상공 (경유지 2)
PLACE_POS = [224.88, 169.98, 38.74]  # 4. 터틀봇에 내려놓는 위치

HOME_POS = [250.0, 0.0, 50.0]  # 복귀용 홈 포지션


def wait_for_done(api, index):
    print("index : ", index)
    print("dType.GetQueuedCmdCurrentIndex(api) : ", dType.GetQueuedCmdCurrentIndex(api))
    while index > dType.GetQueuedCmdCurrentIndex(api)[0]:
        alarms = dType.GetAlarmsState(api)
        has_alarm = any(b != 0 for b in alarms[0])
        print("alarms : ", alarms)
        print("has_alarm : ", has_alarm)

        if has_alarm:
            print(f"⚠️ [ALARM {alarms}] 감지! 해제 중...")
            dType.ClearAllAlarmsState(api)
            dType.SetQueuedCmdStartExec(api)
        dType.dSleep(100)


def dobot_mission(api, conn):
    print("\n--- [START] Dobot Absolute Sequence ---")

    # 속도 설정 (50% 정도가 가장 안정적입니다)
    dType.SetPTPCommonParams(api, 50, 50, isQueued=1)

    # 1단계: 집기 위치로 이동 및 하강
    # (충돌 방지를 위해 먼저 PICK_POS의 상공으로 갔다가 내려가는 것이 좋으나,
    # 일단 주신 좌표 순서대로 진행합니다.)
    print(">> Step 1: Moving to PICK_POS")
    idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *PICK_POS, 0, isQueued=1)[0]
    wait_for_done(api, idx)

    print(">> Action: Suction ON")
    dType.SetEndEffectorSuctionCup(api, True, True, isQueued=1)
    time.sleep(1)

    # 2단계: 집은 후 높이 들어올리기 (경유지 1)
    print(">> Step 2: Lifting to PICK_HIGH")
    idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *PICK_HIGH, 0, isQueued=1)[0]
    wait_for_done(api, idx)

    # 3단계: 터틀봇 쪽 안전 상공으로 이동 (경유지 2)
    # 여기서 Y값이 -15에서 175로 크게 변하므로 이 경유지가 매우 중요합니다.
    print(">> Step 3: Moving to PLACE_READY")
    idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *PLACE_READY, 0, isQueued=1)[0]
    wait_for_done(api, idx)

    # 4단계: 실제로 내려놓기
    print(">> Step 4: Descending to PLACE_POS")
    idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *PLACE_POS, 0, isQueued=1)[0]
    wait_for_done(api, idx)

    print(">> Action: Suction OFF")
    dType.SetEndEffectorSuctionCup(api, True, False, isQueued=1)
    time.sleep(1)

    # ✅ 터틀봇에게 신호 보내기
    print(">> [SIGNAL] Sending 'OK' to TurtleBot.")
    conn.send("OK".encode())

    # 5단계: 홈으로 복귀
    print(">> Step 5: Returning Home")
    idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *HOME_POS, 0, isQueued=1)[0]
    wait_for_done(api, idx)
    print("--- [FINISH] ---")


def main():
    ctrlBot = Dbt.DoBotArm(HOME_POS[0], HOME_POS[1], HOME_POS[2])

    # 시작 전 무조건 알람 클리어
    dType.SetQueuedCmdClear(ctrlBot.api)
    dType.ClearAllAlarmsState(ctrlBot.api)

    # 🚩 계속 영점에서 에러가 난다면:
    # 손으로 로봇을 정중앙(ㄴ자)에 두고 아래 'HOMING'을 실행하세요.
    print("🏠 Homing... (로봇이 스스로 움직이며 영점을 잡습니다)")
    idx = dType.SetHOMECmd(ctrlBot.api, 0, isQueued=1)[0]
    dType.SetQueuedCmdStartExec(ctrlBot.api)
    wait_for_done(ctrlBot.api, idx)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(1)
    print("[SERVER] Dobot Ready. Waiting for 'ARRIVED' signal...")

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