from tasks.celery_tasks import default_task, high_priority_task

# Send task to RabbitMQ queue
result1 = high_priority_task.delay("important data")

# Send task to Redis queue
result2 = default_task.delay("normal data")

# Get results
print(result1.get())
print(result2.get())
