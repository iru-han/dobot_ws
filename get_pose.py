import DobotDllType as dType
import time

# 1. 연결 설정
api = dType.load()
state = dType.ConnectDobot(api, "", 115200)[0]

if state == dType.DobotConnect.DobotConnect_NoError:
    saved_points = []
    print("🚀 티칭 모드를 시작합니다.")
    print("[방법] 1. Unlock 버튼을 누르고 팔을 이동")
    print("       2. 기록하고 싶은 지점에서 'Enter' 키 입력")
    print("       3. 종료하려면 'q' 입력 후 Enter")
    print("-" * 50)

    try:
        while True:
            # 현재 위치 실시간 출력
            pose = dType.GetPose(api)
            x, y, z = pose[0], pose[1], pose[2]
            print(f"\r📌 현재 위치 -> X: {x:7.2f}, Y: {y:7.2f}, Z: {z:7.2f} | 저장된 지점: {len(saved_points)}개", end="")

            # 사용자 입력 확인 (Enter를 치면 기록, q를 치면 종료)
            # input()은 루프를 잠시 멈추기 때문에 정확한 지점 확보에 더 좋습니다.
            cmd = input("\n[명령] Enter(기록) / q(종료): ").lower()

            if cmd == '':
                # 현재 좌표 저장
                saved_points.append([round(x, 2), round(y, 2), round(z, 2)])
                print(f"✅ 지점 저장 완료: {saved_points[-1]}")
            elif cmd == 'q':
                break

    except KeyboardInterrupt:
        pass

    # 종료 후 결과 출력
    print("\n" + "=" * 50)
    print("📂 기록된 좌표 리스트 (복사해서 main.py에 붙여넣으세요)")
    print("=" * 50)
    for i, pt in enumerate(saved_points):
        print(f"지점 {i + 1}: {pt}")
    print("=" * 50)

    dType.DisconnectDobot(api)
else:
    print("❌ 도봇 연결 실패!")