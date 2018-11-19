from multiprocessing import Queue
class Messenger:
    def __init__(self):
        self.mapping = {'ai_controls': Queue()}
        pass

    def send_message(self, mapping_str, func, args=None):
        queue = self.mapping[mapping_str]
        mess = {'func': func}
        if args:
            mess['args'] = args
        try:
            queue.put(mess)
        except Exception as e:
            print("send exception: {}".format(e))
            pass

    def get_message(self, mapping_str):
        queue = self.mapping[mapping_str]
        try:
            data = queue.get(False)
            #print(data)
            return data
        except Exception as e:
            return None