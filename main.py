import DoBotArm as Dbt
import DobotDllType as dType
import time


def wait_and_print_pose(api, index, label):
    """명령이 완료될 때까지 실시간으로 좌표를 출력하며 대기합니다."""
    print(f"\n🏃 [{label}] 이동 시작...")

    while index > dType.GetQueuedCmdCurrentIndex(api)[0]:
        # 실시간 좌표 가져오기
        pose = dType.GetPose(api)
        print(f"\r[현재 위치] X: {pose[0]:.2f}, Y: {pose[1]:.2f}, Z: {pose[2]:.2f}", end="")

        # 알람 체크
        alarms = dType.GetAlarmsState(api)
        if alarms[0] != 0:
            print(f"\n⚠️ 알람 발생! 현재 Z값({pose[2]:.2f})이 이 로봇의 한계치일 가능성이 높습니다.")
            dType.ClearAllAlarmsState(api)
            dType.SetQueuedCmdStartExec(api)
            break  # 알람 발생 시 해당 동작은 중단된 것으로 간주

        dType.dSleep(100)
    print(f"\n✅ [{label}] 이동 완료.")


def main():
    homeX, homeY, homeZ = 250, 0, 50
    ctrlBot = Dbt.DoBotArm(homeX, homeY, homeZ)

    # 초기화 및 홈 잡기
    dType.SetQueuedCmdClear(ctrlBot.api)
    dType.SetHOMEParams(ctrlBot.api, homeX, homeY, homeZ, 0, isQueued=1)

    print("🏠 홈 잡는 중... 로봇이 완전히 멈출 때까지 기다리세요.")
    idx = dType.SetHOMECmd(ctrlBot.api, temp=0, isQueued=1)[0]
    dType.SetQueuedCmdStartExec(ctrlBot.api)
    wait_and_print_pose(ctrlBot.api, idx, "HOME")

    # [좌표 설정]
    # TIP: -132는 너무 깊습니다. -50부터 시작해서 5mm씩 내려보며 한계를 찾으세요.
    PICK_X, PICK_Y, PICK_Z = 200, 0, -20
    PLACE_X, PLACE_Y, PLACE_Z = 150, 150, -20

    try:
        print("\n🚀 시퀀스 시작!")

        # 1-1. 상공 이동
        idx = dType.SetPTPCmd(ctrlBot.api, dType.PTPMode.PTPMOVJXYZMode, PICK_X, PICK_Y, homeZ, 0, isQueued=1)[0]
        wait_and_print_pose(ctrlBot.api, idx, "APPROACH")

        # 1-2. 수직 하강 (한계 측정 구간)
        print(f"\n🎯 목표 하강 높이: {PICK_Z}")
        idx = dType.SetPTPCmd(ctrlBot.api, dType.PTPMode.PTPMOVJXYZMode, PICK_X, PICK_Y, PICK_Z, 0, isQueued=1)[0]
        wait_and_print_pose(ctrlBot.api, idx, "DOWN")

        # 집기 동작
        dType.SetEndEffectorSuctionCup(ctrlBot.api, True, True, isQueued=1)
        time.sleep(1)

        # 1-3. 상승
        idx = dType.SetPTPCmd(ctrlBot.api, dType.PTPMode.PTPMOVJXYZMode, PICK_X, PICK_Y, homeZ, 0, isQueued=1)[0]
        wait_and_print_pose(ctrlBot.api, idx, "LIFT")

        # 2. 터틀봇 이동
        idx = dType.SetPTPCmd(ctrlBot.api, dType.PTPMode.PTPMOVJXYZMode, PLACE_X, PLACE_Y, homeZ, 0, isQueued=1)[0]
        wait_and_print_pose(ctrlBot.api, idx, "MOVE_TO_TURTLE")

        # 3. 내려놓기
        idx = dType.SetPTPCmd(ctrlBot.api, dType.PTPMode.PTPMOVJXYZMode, PLACE_X, PLACE_Y, PLACE_Z, 0, isQueued=1)[0]
        wait_and_print_pose(ctrlBot.api, idx, "PLACE_DOWN")

        dType.SetEndEffectorSuctionCup(ctrlBot.api, True, False, isQueued=1)
        time.sleep(1)

        # 4. 복귀
        ctrlBot.moveHome()
        print("\n✅ 모든 작업 완료!")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    finally:
        dType.SetEndEffectorSuctionCup(ctrlBot.api, False, False, isQueued=0)
        dType.SetQueuedCmdStopExec(ctrlBot.api)


if __name__ == "__main__":
    main()