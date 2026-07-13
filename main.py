import time
import DoBotArm as Dbt
import DobotDllType as dType
from datetime import datetime

# --- [박스 픽업 & 적재 좌표 설정] ---
# pick: 박스가 놓여있는 위치 (X, Y, Z)
# drop: 쌓을 위치 (X, Y, Z) - Z가 점점 높아짐 (아래 박스 위에 쌓이는 구조)
BOXES = [
    {
        "name": "박스1",
        "pick": [113.21, 152.97, -47.18],
        "drop": [161.84, -112.07, -46.59],
    },
    {
        "name": "박스2",
        "pick": [139.33, 149.61, -47.29],
        "drop": [163.98, -113.45, -22.54],
    },
    {
        "name": "박스3",
        "pick": [166.95, 150.36, -47.52],
        "drop": [169.73, -114.20, 2.78],
    },
]

# 이동 중 충돌 방지를 위한 안전 고도 (픽업/드롭 지점 바로 위로 먼저 이동 후 하강)
SAFE_Z_OFFSET = 40  # mm, 필요시 조절

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


def move_to(api, pos, label=""):
    """지정 좌표로 이동 (완료까지 대기)"""
    if label:
        print(f"{get_time()} 📍 [MOVE] {label} 이동 중... {pos}")
    idx = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVJXYZMode, *pos, 0, isQueued=1)[0]
    wait_for_done(api, idx)


def suction(api, on: bool, label=""):
    state_str = "ON (흡착 시작)" if on else "OFF (흡착 해제)"
    print(f"{get_time()} 💡 [ACTION] Suction {state_str} {label}")
    dType.SetEndEffectorSuctionCup(api, True, on, isQueued=1)
    time.sleep(1)


def pick_and_place(api, box):
    name = box["name"]
    pick = box["pick"]
    drop = box["drop"]

    pick_ready = [pick[0], pick[1], pick[2] + SAFE_Z_OFFSET]
    drop_ready = [drop[0], drop[1], drop[2] + SAFE_Z_OFFSET]

    print(f"\n{get_time()} 📦 [BOX] '{name}' 작업 시작")

    # 1. 픽업 위치 상공으로 이동
    move_to(api, pick_ready, f"{name} PICK_READY")

    # 2. 픽업 위치로 하강
    move_to(api, pick, f"{name} PICK_DOWN")

    # 3. 흡착 ON
    suction(api, True, f"({name} 집기)")

    # 4. 다시 상공으로 상승 (이동 중 바닥에 끌리지 않도록)
    move_to(api, pick_ready, f"{name} PICK_UP")

    # 5. 드롭 위치 상공으로 이동
    move_to(api, drop_ready, f"{name} DROP_READY")

    # 6. 드롭 위치로 하강 (박스 쌓을 정확한 높이)
    move_to(api, drop, f"{name} DROP_DOWN")

    # 7. 흡착 OFF
    suction(api, False, f"({name} 놓기)")

    # 8. 다시 상공으로 상승
    move_to(api, drop_ready, f"{name} DROP_UP")

    print(f"{get_time()} ✅ [BOX] '{name}' 작업 완료")


def main():
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

    dType.SetPTPCommonParams(ctrlBot.api, 50, 50, isQueued=1)

    try:
        for box in BOXES:
            pick_and_place(ctrlBot.api, box)

        # 모든 작업 후 홈으로 복귀
        print(f"\n{get_time()} 🏠 [HOME] 작업 완료. 홈 위치로 복귀 중...")
        move_to(ctrlBot.api, HOME_POS, "HOME_POS")

        print(f"\n{get_time()} 🎉 [DONE] 3개 박스 적재 시퀀스 전체 완료!")

    except KeyboardInterrupt:
        print(f"\n{get_time()} 🛑 [STOP] 사용자에 의해 작업이 중단되었습니다.")
    except Exception as e:
        print(f"{get_time()} ❌ [FATAL] 오류 발생: {e}")


if __name__ == "__main__":
    main()