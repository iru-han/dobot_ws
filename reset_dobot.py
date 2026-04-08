import DobotDllType as dType
import time

# 1. API 로드
api = dType.load()

# 2. 연결 (포트 자동 탐색)
print("🔍 도봇 연결 시도 중...")
state = dType.ConnectDobot(api, "", 115200)[0]

if state == dType.DobotConnect.DobotConnect_NoError:
    print("✅ 연결 성공!")

    # 3. 알람 해제
    print("🧹 알람 및 큐 초기화 중...")
    dType.ClearAllAlarmsState(api)
    dType.SetQueuedCmdClear(api)

    # 4. 강제 시작 명령
    dType.SetQueuedCmdStartExec(api)
    print("🚀 실행 명령 전송 완료!")

    # 5. 현재 상태 확인
    time.sleep(1)
    pose = dType.GetPose(api)
    print(f"📍 현재 로봇 좌표: X={pose[0]:.2f}, Y={pose[1]:.2f}, Z={pose[2]:.2f}")

    dType.DisconnectDobot(api)
else:
    if state == dType.DobotConnect.DobotConnect_Occupied:
        print("⚠️ 에러: 포트가 이미 사용 중입니다! (DobotLab이나 다른 프로그램을 끄세요)")
    else:
        print(f"❌ 에러: 도봇을 찾을 수 없습니다. (에러코드: {state})")