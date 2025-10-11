def is_even(number):
    """
    Check if a number is even.

    Args:
        number: An integer to check

    Returns:
        bool: True if the number is even, False otherwise
    """
    return number % 2 == 0


def identify_even_numbers(numbers):
    """
    Identify even numbers from a list of numbers.

    Args:
        numbers: A list of integers

    Returns:
        list: A list containing only the even numbers
    """
    return [num for num in numbers if is_even(num)]


def main():
    # Example usage
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 23, 42]

    print("Original numbers:", numbers)

    # Get even numbers
    even_numbers = identify_even_numbers(numbers)
    print("Even numbers:", even_numbers)

    # Check individual numbers
    print("\nChecking individual numbers:")
    for num in [7, 8, 15, 24]:
        print(f"{num} is {'even' if is_even(num) else 'odd'}")


if __name__ == "__main__":
    main()
