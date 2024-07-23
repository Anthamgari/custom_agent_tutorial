import os
import yaml
import json
import requests
from colorama import init, Fore

# Initialize colorama and auto-reset color after each print
init(autoreset=True)

def load_config(file_path):
    """Load configuration from a YAML file and set environment variables."""
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
        for key, value in config.items():
            os.environ[key] = value

def load_tasks(file_path='plan.json'):
    """Load tasks from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read().strip()
            if content:  # Check if the file is not empty
                return json.loads(content)
    return []

def save_tasks(tasks, file_path='plan.json'):
    """Save tasks to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(tasks, file, indent=4)

class Agent:
    def __init__(self, model, temperature=0, max_tokens=1000, planning_agent_prompt=None, verbose=False):
        load_config('config.yaml')
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.url = 'https://api.openai.com/v1/chat/completions'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.planning_agent_prompt = planning_agent_prompt
        self.model = model
        self.verbose = verbose

    def run_planning_agent(self, query, current_tasks):
        """Run the planning agent with the given query and current tasks."""
        system_prompt = self.planning_agent_prompt.format(
            user_input=query,
            current_tasks=json.dumps(current_tasks)
        )

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": query},
                         {"role": "system", "content": system_prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        response = requests.post(self.url, headers=self.headers, json=data, timeout=180)
        response_dict = response.json()
        print(response_dict['choices'])
        content = response_dict['choices'][0]['message']['content']
        print(Fore.GREEN + f"Planning Agent: {content}")

        return content

    def execute(self, iterations=5):
        """Execute the planning agent to handle user queries and manage tasks."""
        query = input("Enter your query: ")
        tasks = load_tasks()
    
        meets_requirements = False
        plan = None
        iterations_count = 0

        while not meets_requirements and iterations_count < iterations:
            iterations_count += 1  
            plan = self.run_planning_agent(query, tasks)

            # Append the new task with the plan
            if plan:
                tasks.append({"task": query, "plan": plan})
                save_tasks(tasks)
                print(Fore.CYAN + f"Final Response: {plan}")
                meets_requirements = True

if __name__ == '__main__':
    planning_agent_prompt = (
        "You are an AI planning agent working with a task management system.\n"
        "Your job is to decide on the action based on the user's input.\n"
        "From the user's query, determine whether the action involves adding a task, marking a task as completed, or listing tasks.\n"
        "If the action involves listing tasks, you should provide a clear list of the current tasks.\n\n"
        "Here is the user's input: {user_input}\n"
        "Here is the current list of tasks: {current_tasks}\n"
        "Based on this, provide a plan for the action, and if it involves listing tasks, indicate that explicitly."
    )

    agent = Agent(model="gpt-3.5-turbo",
                  planning_agent_prompt=planning_agent_prompt,
                  verbose=True
                  )
    agent.execute()
