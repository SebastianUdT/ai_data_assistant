import argparse

from pydantic import ValidationError

from src.llm import ask_llm, parse_customer


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Data Assistant"
    )

    parser.add_argument(
        "prompt",
        help="Question or request for the assistant",
    )

    args = parser.parse_args()

    response = ask_llm(args.prompt)

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