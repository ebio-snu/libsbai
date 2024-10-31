# libsbapi
제4회 스마트 농업 인공지능 경진대회용 라이브러리

## 소개
제4회 스마트농업 인공지능 경진대회 API 를 활용하기위한 파이썬라이브러리이다.
pyModbusTCP (https://github.com/sourceperl/pyModbusTCP) 의 코드를 활용하였다.

별도의 API 문서에서 소개되겠지만, 경진대회 API 의 컨텐츠는 KS X 3267, KS X 3286, KS X 3288 스마트온실 통신 표준을 기반으로 구성되었다. 

## 사용법

### 초기화

팀별로 할당된 키를 사용하여 모듈을 초기화한다. access-key 는 팀별로 할당되는 비밀키이다.

client = SBAPIClient("access-key")

### 데이터 읽기

데이터를 읽어오기 위해서는 read_holding_registers 함수를 사용한다. 

reg = client.read_holding_registers(시작주소, 개수, 유닛아이디)

정상적인 읽기가 되었다면, reg 는 읽어온 레지스터의 배열이다.

### 데이터 쓰기

데이터를 쓰기 위해서는 write_multiple_registers 함수를 사용한다.

client.write_multiple_registers(시작주소, [쓸 데이터 배열], 유닛아이디)

정상적인 쓰기가 되었다면, True 를 리턴한다.

## 예시

### 센서값 읽어오기
3번 슬레이브(유닛아이디 3)에 있는 온도, 습도 데이터를 읽고자 한다면 다음과 같은 코드를 작성하여 활용할 수 있다.  이 예시에서는 struct 패키지를 사용한다.

examples/read_sensor.py 에 샘플이 있다. 
테스트는 현재 위치에서 다음과 같이 한다.

python3 -m examples.read_sensor

### 제어권 확인 및 바꾸기
인공지능을 활용하여 제어를 수행할때는 노드의 제어권을 변경해야한다. 

examples/control_priv.py 에 샘플이 있다. 
테스트는 현재 위치에서 다음과 같이 한다.

python3 -m examples.control_priv

### 스위치 작동시키기
4번 슬레이브(유닛아이디 4)에 있는 유동팬 1을 켰다가 끈다.

examples/switch.py 에 샘플이 있다. 
테스트는 현재 위치에서 다음과 같이 한다.

python3 -m examples.switch
    

