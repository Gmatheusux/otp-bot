import time
from core.decision_thread import DecisionThread

def get_string_state():
    return {'hp': '50', 'monsters': '3'}

def test_decision_thread_string_state():
    dt = DecisionThread(get_string_state)
    dt.start()
    time.sleep(1)
    dt.stop()

if __name__ == "__main__":
    test_decision_thread_string_state()
    print("Done!")
