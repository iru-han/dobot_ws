import DoBotArm as Dbt
import DobotDllType as dType # 직접 제어를 위해 필요
import time

# 1. 도봇 연결 (홈 좌표 설정)
homeX, homeY, homeZ = 250, 0, 50
print("로봇 연결 시도 중...")
ctrlBot = Dbt.DoBotArm(homeX, homeY, homeZ)

# 2. 대기열(Queue) 실행 강제 시작 (중요 ⭐)
# 깃허브 코드들 중 많은 것들이 이 명령어를 빠뜨려서 안 움직입니다.
dType.SetQueuedCmdStartExec(ctrlBot.api)
print("대기열 실행 시작!")

# 3. 테스트 이동
print("이동 명령 전송...")
# 현재 위치에서 살짝 옆으로 이동 (x, y)
ctrlBot.moveArmXY(200, 50)
time.sleep(2) # 이동할 시간 확보

# 4. 홈으로 돌아오기
print("홈으로 복귀...")
ctrlBot.moveHome()

print("테스트 종료!")