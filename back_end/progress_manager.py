import threading

class ProgressManager:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    def create_job(self, job_id):
        with self.lock:
            self.jobs[job_id] = {
                'status': 'started',
                'progress': [],
                'result': None,
                'error': None,
                'no_of_dialogues' : None
            }
    
    def update_progress(self, job_id, message):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['progress'].append(message)

    def set_status(self, job_id, status):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['status'] = status

    def set_result(self, job_id, result):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['result'] = result
                self.jobs[job_id]['status'] = 'completed'

    def set_error(self, job_id, error_message):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['error'] = error_message
                self.jobs[job_id]['type'] = 'error'
                self.jobs[job_id]['status'] = 'failed'

    def get_progress(self, job_id):
        with self.lock:
            return self.jobs.get(job_id, None)
