def is_even(number):
    """Check if a number is even."""
    return number % 2 == 0


def find_even_numbers(numbers):
    """Return a list of even numbers from the input list."""
    return [num for num in numbers if num % 2 == 0]


# Example usage
if __name__ == "__main__":
    # Test with a list of numbers
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    print("Numbers:", numbers)
    print("Even numbers:", find_even_numbers(numbers))

    # Test individual numbers
    print(f"\nIs 7 even? {is_even(9)}")
    print(f"Is 8 even? {is_even(3)}")
