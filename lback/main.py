import sys
from lback.commands import Commands

def main():
    if len(sys.argv) < 2:
        print("Usage: Lback <command>")
        Commands.help()
        return

    command = sys.argv[1]

    if command == "startproject":
        if len(sys.argv) > 2:
            project_name = sys.argv[2]
            Commands.startproject(project_name)
        else:
            print("Usage: Lback startproject <project_name>")
    
    elif command == "startapp":
        if len(sys.argv) > 2:
            app_name = sys.argv[2]
            Commands.startapp(app_name)
        else:
            print("Usage: Lback startapp <app_name>")
    

    elif command == "runserver":
        Commands.runserver()
 
    elif command == "migrate":
        Commands.migrate()

    elif command == "makemigrations":
        Commands.makemigrations()


    elif command == "test":
        Commands.test()


    elif command == "collectstatic":
        Commands.collectstatic()


    elif command == "help":
        Commands.help()

 
    else:
        print(f"Unknown command: {command}")
        print("Use 'Lback help' for a list of available commands.")
        Commands.help()

if __name__ == "__main__":
    main()
