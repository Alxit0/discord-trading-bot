
def teste_database():
    from database.database import InMemoryDatabase
    file_path = "./data.json"
    db = InMemoryDatabase(file_path)

    db.display_all()
    db.save_data("../data.json")
    
    print("Database OK.")


def main():
    teste_database()

if __name__ == '__main__':
    main()
