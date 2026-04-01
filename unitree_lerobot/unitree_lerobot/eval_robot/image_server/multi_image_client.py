import cv2
import zmq
import numpy as np
import time
import struct
from collections import deque
from multiprocessing import shared_memory


class MultiImageClient:
    def __init__(
        self,
        tv_img_shape=None,
        tv_img_shm_name=None,
        wrist_img_shape=None,
        wrist_img_shm_name=None,
        image_show=False,
        server_address="127.0.0.1",
        head_port=55555,
        left_wrist_port=55556,
        right_wrist_port=55557,
        Unit_Test=False,
    ):
        """
        tv_img_shape: User's expected head camera resolution shape (H, W, C).
        tv_img_shm_name: Shared memory is used to easily transfer images across processes.
        wrist_img_shape: User's expected wrist camera resolution shape (H, W * 2, C) because it holds left and right.
        wrist_img_shm_name: Shared memory is used to easily transfer images.
        """
        self.running = True
        self._image_show = image_show
        self._server_address = server_address
        
        self.head_port = head_port
        self.left_wrist_port = left_wrist_port
        self.right_wrist_port = right_wrist_port

        self.tv_img_shape = tv_img_shape
        self.wrist_img_shape = wrist_img_shape

        self.tv_enable_shm = False
        if self.tv_img_shape is not None and tv_img_shm_name is not None:
            self.tv_image_shm = shared_memory.SharedMemory(name=tv_img_shm_name)
            self.tv_img_array = np.ndarray(tv_img_shape, dtype=np.uint8, buffer=self.tv_image_shm.buf)
            self.tv_enable_shm = True

        self.wrist_enable_shm = False
        if self.wrist_img_shape is not None and wrist_img_shm_name is not None:
            self.wrist_image_shm = shared_memory.SharedMemory(name=wrist_img_shm_name)
            self.wrist_img_array = np.ndarray(wrist_img_shape, dtype=np.uint8, buffer=self.wrist_image_shm.buf)
            self.wrist_enable_shm = True

        self._enable_performance_eval = Unit_Test

    def _decode_msg(self, message):
        if self._enable_performance_eval:
            header_size = struct.calcsize("dI")
            try:
                jpg_bytes = message[header_size:]
            except struct.error as e:
                print(f"[MultiImage Client] Error unpacking header: {e}, discarding message.")
                return None
        else:
            jpg_bytes = message

        np_img = np.frombuffer(jpg_bytes, dtype=np.uint8)
        current_image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        if current_image is None:
            print("[MultiImage Client] Failed to decode image.")
        return current_image

    def _close(self):
        self.head_socket.close()
        if self.wrist_enable_shm:
            self.left_wrist_socket.close()
            self.right_wrist_socket.close()
        self._context.term()
        if self._image_show:
            cv2.destroyAllWindows()
        print("MultiImage client has been closed.")

    def receive_process(self):
        self._context = zmq.Context()
        self.poller = zmq.Poller()

        self.head_socket = self._context.socket(zmq.SUB)
        self.head_socket.connect(f"tcp://{self._server_address}:{self.head_port}")
        self.head_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.poller.register(self.head_socket, zmq.POLLIN)

        if self.wrist_enable_shm:
            self.left_wrist_socket = self._context.socket(zmq.SUB)
            self.left_wrist_socket.connect(f"tcp://{self._server_address}:{self.left_wrist_port}")
            self.left_wrist_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            self.poller.register(self.left_wrist_socket, zmq.POLLIN)

            self.right_wrist_socket = self._context.socket(zmq.SUB)
            self.right_wrist_socket.connect(f"tcp://{self._server_address}:{self.right_wrist_port}")
            self.right_wrist_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            self.poller.register(self.right_wrist_socket, zmq.POLLIN)

        print("\nMultiImage client has started, waiting to receive data on multiple ports...")
        try:
            while self.running:
                socks = dict(self.poller.poll(timeout=100))

                if self.head_socket in socks and socks[self.head_socket] == zmq.POLLIN:
                    msg = self.head_socket.recv()
                    img = self._decode_msg(msg)
                    if img is not None and self.tv_enable_shm:
                        np.copyto(self.tv_img_array, np.array(img))

                if self.wrist_enable_shm:
                    if self.left_wrist_socket in socks and socks[self.left_wrist_socket] == zmq.POLLIN:
                        msg = self.left_wrist_socket.recv()
                        img = self._decode_msg(msg)
                        if img is not None:
                            w = img.shape[1]
                            np.copyto(self.wrist_img_array[:, :w], np.array(img))

                    if self.right_wrist_socket in socks and socks[self.right_wrist_socket] == zmq.POLLIN:
                        msg = self.right_wrist_socket.recv()
                        img = self._decode_msg(msg)
                        if img is not None:
                            w = img.shape[1]
                            np.copyto(self.wrist_img_array[:, w:2*w], np.array(img))

        except KeyboardInterrupt:
            print("MultiImage client interrupted by user.")
        except Exception as e:
            print(f"[MultiImage Client] An error occurred while receiving data: {e}")
        finally:
            self._close()

if __name__ == "__main__":
    client = MultiImageClient(image_show=False, server_address="127.0.0.1", Unit_Test=False)
    client.receive_process()
