from crewai import Crew, Process

def create_crew(agents, tasks, task_callback):
    return Crew(
        agents=agents,
        tasks=tasks,
        verbose=False,
        task_callback=task_callback,
        process=Process.sequential,
    )
