

class TaskService:
    def __init__(self, task_repository):
        self.task_repository = task_repository

    def create_task(self, task_data):
        return self.task_repository.create(task_data)

    def get_task(self, task_id):
        return self.task_repository.get(task_id)

    def update_task(self, task_id, task_data):
        return self.task_repository.update(task_id, task_data)

    def delete_task(self, task_id):
        return self.task_repository.delete(task_id)