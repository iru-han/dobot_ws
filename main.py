import socket
import time
import DoBotArm as Dbt
import DobotDllType as dType
from datetime import datetime

# --- [티칭 좌표 설정] ---
PICK_READY = [122.85, 166.33, 21.06]
PICK_DOWN = [122.9, 170.8, -53.54]
PICK_HIGH = [274.79, 3.94, 109.11]
DROP_POS = [250.0, 0.0, 50.0]
# DROP_POS = [267.49, 7.17, 30.41]
HOME_POS = [250.0, 0.0, 50.0]


def get_time():
    """로그용 현재 시간 포맷팅"""
    return datetime.now().strftime("[%H:%M:%S]")


def wait_for_done(api, index):
    while index > dType.GetQueuedCmdCurrentIndex(api)[0]:
        alarms = dType.GetAlarmsState(api)
        if any(alarms[0]):
            print(f"{get_time()} ⚠️ [ROBOT ALARM] {alarms} 발생! 강제 해제 시도 중...")
            dType.ClearAllAlarmsState(api)
            dType.SetQueuedCmdStartExec(api)
        dType.dSleep(100)


def dobot_mission(api, conn=None):
    print(f"\n{get_time()} 🦾 [MISSION] 시퀀스 시작")
    dType.SetPTPCommonParams(api, 50, 50, isQueued=1)

    # 동작 단계 리스트 (가독성을 위해 반복문 처리 가능하나 직관성을 위해 유지)
    steps = [
        ("PICK_READY", PICK_READY),
        ("PICK_DOWN", PICK_DOWN),
        ("PICK_HIGH", PICK_HIGH),
        ("DROP_POS", DROP_POS),
        ("HOME_POS", HOME_POS)
    ]

    for name, pos in steps:
        print(f"{get_time()} 📍 [MOVE] {name} 이동 중... {pos}")
        idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *pos, 0, isQueued=1)[0]
        wait_for_done(api, idx)

        # 흡착 컵 제어 (특정 단계에서 실행)
        if name == "PICK_DOWN":
            print(f"{get_time()} 💡 [ACTION] Suction ON (흡착 시작)")
            dType.SetEndEffectorSuctionCup(api, True, True, isQueued=1)
            time.sleep(1)
        elif name == "DROP_POS":
            print(f"{get_time()} 💡 [ACTION] Suction OFF (흡착 해제)")
            dType.SetEndEffectorSuctionCup(api, True, False, isQueued=1)
            time.sleep(1)

    # ✅ 통신 로그: 신호 전송 확인
    if conn:
        print(f"{get_time()} 📡 [NET] 터틀봇에게 완료 신호('OK') 전송 준비 중...")
        try:
            conn.send("OK".encode())
            print(f"{get_time()} ✅ [NET] 완료 신호 전송 성공!")
        except Exception as e:
            print(f"{get_time()} ❌ [NET] 신호 전송 실패: {e}")

    print(f"{get_time()} ✨ [MISSION] 시퀀스 종료\n")


def main():
    # 로봇 초기화
    print(f"{get_time()} 🤖 도봇 팔 연결 및 초기화 중...")
    ctrlBot = Dbt.DoBotArm(HOME_POS[0], HOME_POS[1], HOME_POS[2])
    dType.SetQueuedCmdClear(ctrlBot.api)
    dType.ClearAllAlarmsState(ctrlBot.api)

    # 영점 잡기
    print(f"{get_time()} 🏠 [HOME] 영점 잡기 시작 (Homing...)")
    idx = dType.SetHOMECmd(ctrlBot.api, 0, isQueued=1)[0]
    dType.SetQueuedCmdStartExec(ctrlBot.api)
    wait_for_done(ctrlBot.api, idx)
    print(f"{get_time()} 🏠 [HOME] 영점 잡기 완료!")

    # --- [서버 통신 설정] ---
    HOST = '0.0.0.0'
    PORT = 9999

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 포트 재사용 설정 (서버 재시작 시 에러 방지)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # --- [테스트 모드: 소켓 없이 바로 실행] ---
    """
    print("\n📢 소켓 신호 없이 바로 동작 테스트를 시작합니다.")
    dobot_mission(ctrlBot.api)
    """

    try:
        server.bind((HOST, PORT))
        server.listen(1)
        print("-" * 60)
        print(f"{get_time()} 🌐 [SERVER] 도봇 서버 대기 중...")
        print(f"{get_time()} 🌐 [INFO] IP: {HOST} | PORT: {PORT}")
        print("-" * 60)

        while True:
            # 클라이언트 접속 대기
            conn, addr = server.accept()
            print(f"\n{get_time()} 🔗 [CONN] 클라이언트 연결됨! (터틀봇 IP: {addr[0]})")

            try:
                # 데이터 수신
                data = conn.recv(1024).decode().strip()
                print(f"{get_time()} 📥 [DATA] 수신된 데이터: '{data}'")

                if data == "ARRIVED":
                    print(f"{get_time()} 🎯 [MATCH] 'ARRIVED' 신호 확인. 미션을 시작합니다.")
                    dobot_mission(ctrlBot.api, conn)
                else:
                    print(f"{get_time()} ❓ [UNKNOWN] 정의되지 않은 신호입니다: '{data}'")

            except Exception as e:
                print(f"{get_time()} ⚠️ [ERROR] 통신 중 오류 발생: {e}")

            finally:
                conn.close()
                print(f"{get_time()} 🔌 [DISCONN] 클라이언트 연결 종료. 다음 신호 대기...")

    except KeyboardInterrupt:
        print(f"\n{get_time()} 🛑 [STOP] 사용자에 의해 서버가 중단되었습니다.")
    except Exception as e:
        print(f"{get_time()} ❌ [FATAL] 서버 오류: {e}")
    finally:
        server.close()
        print(f"{get_time()} ⚰️ [EXIT] 서버 시스템 종료")


if __name__ == "__main__":
    main()