import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import socket
import time

# [설정] 노트북 정보
LAPTOP_IP = '192.168.0.33' 
PORT = 9999

class TurtlebotMissionNode(Node):
    def __init__(self):
        super().__init__('turtlebot_mission_node')
        # 네임스페이스 반영된 토픽 이름 (/r3/cmd_vel)
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        time.sleep(1.0) # 퍼블리셔 안정화 대기
        self.run_mission()

    def move_turtlebot(self, speed, duration, label):
        """지정된 속도로 지정된 시간만큼 이동하는 함수"""
        print(f">> {label}: 속도 {speed}로 {duration}초간 이동 시작")
        msg = Twist()
        msg.linear.x = speed
        
        start_time = time.time()
        while rclpy.ok() and (time.time() - start_time < duration):
            self.publisher.publish(msg)
            time.sleep(0.1) # 10Hz 주기로 발행
            
        # 정지 명령
        self.publisher.publish(Twist())
        print(f">> {label}: 정지 완료.")

    def run_mission(self):
        # 1. 도봇 앞으로 이동 (몸통 2개 거리만큼 0.01 속도로)
        # 약 27.6초 동안 이동 (0.01m/s * 27.6s = 0.276m)
        self.move_turtlebot(speed=0.01, duration=27.6, label="도봇으로 접근 중")

        # 2. 소켓 통신 (신호 보내기)
        print(">> Arrived at Dobot. Sending signal to Laptop...")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(60) # 도봇 작업 시간을 고려하여 타임아웃 넉넉히 설정
            s.connect((LAPTOP_IP, PORT))
            
            # 도착 신호 전송
            s.send("ARRIVED".encode())
            print(">> Waiting for Dobot to load object...")
            
            # 도봇으로부터 작업 완료(OK) 신호를 대기
            response = s.recv(1024).decode()
            
            if response == "OK":
                print(">> [SIGNAL RECEIVED] Dobot task finished!")
                
                # 3. 추가 이동 (몸통 반개 거리만큼 0.01 속도로)
                # 약 6.9초 동안 이동 (0.01m/s * 6.9s = 0.069m)
                self.move_turtlebot(speed=0.01, duration=6.9, label="추가 목적지로 이동 중")
                print(">> [MISSION COMPLETE] Arrived at final destination.")
            
            s.close()
        except Exception as e:
            print(f">> [ERROR] Connection or Task failed: {e}")

def main():
    rclpy.init()
    node = TurtlebotMissionNode()
    # 미션 완료 후 노드 종료
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
