class Messenger:

    def send_message(self, queue, func, args=None):
        mess = {'func': func}
        if args:
            mess['args'] = args
        try:
            queue.put(mess)
        except Exception as e:
            print("send exception: {}".format(e))
            pass

    def get_message(self, queue):
        try:
            data = queue.get(False)
            #print(data)
            return data
        except Exception as e:
            return None