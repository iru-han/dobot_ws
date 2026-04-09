import DobotDllType as dType
import time
import sys

# 1. 연결 설정
api = dType.load()
state = dType.ConnectDobot(api, "", 115200)[0]

if state == dType.DobotConnect.DobotConnect_NoError:
    print("✅ 도봇 연결 성공!")

    # [추가] 초기화 및 알람 해제
    dType.SetQueuedCmdClear(api)
    dType.ClearAllAlarmsState(api)

    # [핵심] 영점 잡기 (Homing)
    # 로봇이 삐- 소리를 내며 제자리로 돌아올 때까지 기다리세요.
    print("🏠 영점(Home)을 잡는 중입니다... 잠시만 기다려주세요.")
    idx = dType.SetHOMECmd(api, 0, isQueued=1)[0]
    dType.SetQueuedCmdStartExec(api)

    # 영점이 완료될 때까지 대기
    while idx > dType.GetQueuedCmdCurrentIndex(api)[0]:
        dType.dSleep(100)

    print("\n🚀 영점 완료! 이제 티칭을 시작합니다.")
    print("-" * 50)
    print("[방법] 1. Unlock 버튼을 누르고 팔을 이동")
    print("       2. 기록하고 싶은 지점에서 'Enter' 입력")
    print("       3. 'q' 입력 시 종료 및 리스트 출력")
    print("-" * 50)

    saved_points = []
    try:
        while True:
            # 실시간 좌표 가져오기
            pose = dType.GetPose(api)
            x, y, z = pose[0], pose[1], pose[2]

            # 알람 발생 여부 실시간 체크
            alarms = dType.GetAlarmsState(api)
            # 바이트 배열 안에 0이 아닌 값이 하나라도 있는지 확인
            has_alarm = any(b != 0 for b in alarms[0])

            print("alarms : ", alarms)
            print("has_alarm : ", has_alarm)

            alarm_msg = "OK" if not has_alarm else "⚠️ ALARM"
            print("alarm_msg : ", alarm_msg)

            # 만약 알람이 진짜 있다면 상세 코드 출력 (옵션)
            if has_alarm:
                alarm_msg += f" (Code: {alarms[0].hex()})"

            print(f"\r📌 X: {x:7.2f}, Y: {y:7.2f}, Z: {z:7.2f} | STATUS: {alarm_msg}", end="")

            # 명령 입력
            cmd = input().lower()
            print("cmd : ", cmd)

            if cmd == '':
                # 수정된 부분: alarms[0] != 0 대신 has_alarm 변수 사용
                if has_alarm:
                    print("\n❌ ERROR! ALARM ACTIVE. CANNOT SAVE")
                    dType.ClearAllAlarmsState(api)
                    continue

                saved_points.append([round(x, 2), round(y, 2), round(z, 2)])
                print(f"\n✅ POSE {len(saved_points)} SAVE SUCCESS: {saved_points[-1]}")

            elif cmd == 'q':
                break
    except Exception as e:
        print(f"\nERROR: {e}")

    # 결과 출력
    print("\n" + "=" * 50)
    print("📂 POSE LIST!")
    print("=" * 50)
    for i, pt in enumerate(saved_points):
        print(f"POINT_{i + 1} = {pt}")
    print("=" * 50)

    dType.DisconnectDobot(api)
else:
    print("❌ 도봇 연결 실패!")