from timeit import default_timer as timer

class DebugTimer:
    def __init__(self):
        self.prev_time = None
        self.start_time = None

    def start(self):
        self.prev_time = timer()
        self.start_time = timer()

    def print(self, message):
        if self.prev_time is not None:
            current_time = timer()
            elapsed_time = current_time - self.prev_time
            self.prev_time = current_time
            print(f"{message}: 経過時間 {elapsed_time}秒, From Timer Start :{current_time - self.start_time} Seconds")
        else:
            print("タイマーが開始されていません。")

