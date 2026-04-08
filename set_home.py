import DobotDllType as dType

api = dType.load()
dType.ConnectDobot(api, "", 115200)

# 1. 모든 알람 싹 비우기
dType.ClearAllAlarmsState(api)
dType.SetQueuedCmdClear(api)

# 2. 홈 위치 설정 (현재 위치를 기준으로 영점을 잡는 게 아니라, 정해진 홈으로 찾아가게 함)
# 이 명령을 내리면 로봇이 혼자 막 움직이면서 '삐-' 소리가 날 때까지 기다려야 합니다.
print("🏠 홈 잡는 중... 로봇이 멈출 때까지 건드리지 마세요!")
dType.SetHOMECmd(api, temp=0, isQueued=1)
dType.SetQueuedCmdStartExec(api)

# 홈 잡기가 끝날 때까지 충분히 대기 (약 10~20초)