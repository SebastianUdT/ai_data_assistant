from pydantic import ValidationError

from llm import ask_llm, parse_customer


def main() -> None:
    prompt = input("Ask something: ")

    response = ask_llm(prompt)

    if "name" in response:
        try:
            customer = parse_customer(response)

            print("\nCustomer:")
            print(f"Name: {customer.name}")
            print(f"Email: {customer.email}")
            print(f"Purchase: ${customer.purchase_amount}")

        except ValidationError as error:
            print("\nInvalid customer data:")
            print(error)

    else:
        print("\nAssistant:")
        print(response["message"])


if __name__ == "__main__":
    main()