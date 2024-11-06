import inquirer
import argparse

def developpement_menu():
    pass

def menu():
    questions = [
    inquirer.List('size',
                    message="What size do you need?",
                    choices=['Jumbo', 'Large', 'Standard', 'Medium', 'Small', 'Micro'],
                ),
    ]
    answers = inquirer.prompt(questions)
    print(answers["size"])

if __name__=='__main__':
    
    parser = argparse.ArgumentParser(description='Add some arguments.')
    
    # Argument optionnel : --dev
    parser.add_argument('--dev', action='store_true',
                        help='enable development mode')

    # Argument optionnel : --menu
    parser.add_argument('--menu', action='store_true',
                        help='show menu')

    # Argument optionnel : --test
    parser.add_argument('--test', action='store_true',
                        help='enable test mode')
    args = parser.parse_args()
    print(args.sum(args.integers))
    
    if args.dev:
        print("Development mode active.")
        print("Sum of integers:", sum(args.integers))
    elif args.menu:
        print("Menu mode active.")
        print("Max of integers:", max(args.integers))
    elif args.test:
        print("Test mode active.")
        print("Count of integers:", len(args.integers))
    else:
        print("No special mode selected.")
    
    #menu()