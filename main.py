import inquirer
import argparse
import lib.utils as utils
import lib.test_utils as t_utils

def developpement_menu():
    pass

def menu():
    questions = [
    inquirer.List('code',
                    message="Qu'est ce que vous voulez charger ?",
                    choices=['Création BDD POI', 'Création BDD prix Paris', 'Nettoyage BDD', 'Jointure BDD', 'Entrainement Model', 'Application - AppartVisor'],
                ),
    ]
    answers = inquirer.prompt(questions)
    print(answers["code"])

if __name__=='__main__':
    
    parser = argparse.ArgumentParser(description='Add some arguments.')
    
    # Argument optionnel : --dev
    parser.add_argument('--dev', action='store_true',
                        help='enable development mode')

    # Argument optionnel : --menu
    parser.add_argument('--menu', action='store_true',
                        help='show menu')

    # Argument optionnel : --test
    parser.add_argument('--test', type=str,
                        help='enable test mode')
    args = parser.parse_args()
    
    if args.dev:
        print("Development mode active.")
        
    elif args.menu:
        print("Menu mode active.")
        menu()
        
    elif args.test:
        print("Test mode active.")
        print(f"test : {args.test}")
        if args.test == 'simplify_ban':
            utils.simplify_ban(input_file='AppartVisor\\data\\adresses-ban.csv', output_file='AppartVisor\\data\\simplified_ban.csv')

        if args.test == 'get_data_from_referenceloyer':
            utils.get_data_from_referenceloyer(ban_path='AppartVisor\\data\\simplified_ban.csv',output_file='AppartVisor\\data\\loyers_paris_adresses.csv')
    else:
        print("No special mode selected.")
    
    #menu()