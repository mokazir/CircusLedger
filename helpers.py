from functools import wraps
from re import match as regexmatch

from flask import redirect, render_template, session


def apology(message, code=400):
    """
    Generate an apology message.

    This function takes a message and an optional code as input parameters.
    It then escapes any special characters in the message using the `escape()` helper function.
    Finally, it renders the apology template `apology.html` with the code as the top variable
    and the escaped message as the bottom variable.

    Parameters:
        message (str): The message to be displayed in the apology.
        code (int, optional): The HTTP status code to be returned. Defaults to 400.

    Returns:
        tuple: A tuple containing the rendered apology template and the HTTP status code.

    Example:
        apology("Sorry, an error occurred.", code=500)

    Note:
        The `escape()` function is a helper function defined within this function.
    """

    # Helper function to escape special characters in a given string
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        # Define special characters and their corresponding escapes
        special_characters = [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]

        # Replace special characters with their escapes
        for old, new in special_characters:
            s = s.replace(old, new)

        return s

    # Render the apology template with the code and escaped message
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorator function that checks if the user is logged in and has a valid company ID.

    Parameters:
        f (function): The function to be decorated.

    Returns:
        function: The decorated function.
    """
    @wraps(f)  # Use the @wraps decorator to preserve the name and docstring of the original functio
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if not session.get("user_id"):
            return redirect("/login")
        # Check if user has a valid company ID
        if not session.get("company_id"):
            return redirect("/compregister")
        # If both conditions are met, execute the original function
        return f(*args, **kwargs)

    # Return the decorated function
    return decorated_function


def user_required(f):
    """
    Decorator that checks if a user is logged in before executing the decorated function.

    Parameters:
        f (function): The function to be decorated.

    Returns:
        function: The decorated function.

    """
    # Use the @wraps decorator to preserve the name and docstring of the original function
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if not session.get("user_id"):
            # If not, redirect the user to the login page
            return redirect("/login")
        # If the user is logged in, execute the original function
        return f(*args, **kwargs)

    # Return the decorated function
    return decorated_function


def inr(value):
    """
    Formats a given value as an Indian Rupee currency string.

    Args:
        value (float): The value to be formatted.

    Returns:
        str: The formatted currency string in the format "₹X,XXX.XX".
    """
    # Check if the value is not None or zero
    if value:
        # Format the value as a currency string with Indian Rupee symbol and comma-separated thousands
        return f"₹{value:,.2f}"


def is_valid_phno(phone_number):
    """
    Check if the given phone number is a valid Indian phone number.

    Args:
        phone_number (str): The phone number to be validated.

    Returns:
        bool: True if the phone number is valid, False otherwise.
    """
    # Pattern to match a valid Indian phone number
    pattern = r"^[6-9][0-9]{9}$"
    # Check if the phone number matches the pattern
    return regexmatch(pattern, phone_number) is not None


def is_valid_password(password):
    """
    Checks if a password is valid.

    Parameters:
        password (str): The password to be checked.

    Returns:
        bool: True if the password is valid, False otherwise.
    """
    # Pattern to match a valid password
    pattern = r"^(?=.*[A-Za-z\d])(?=.*[\d\W\s])(?=.*[A-Za-z\W\s])[A-Za-z\d\s\W]{8,24}$"
    # Check if the password matches the pattern
    return regexmatch(pattern, password) is not None


def is_valid_email(email):
    """
    Check if an email address is valid.

    Args:
        email (str): The email address to be validated.

    Returns:
        bool: True if the email address is valid, False otherwise.
    """
    # Pattern to match a valid email address
    pattern = r"^[\w!#$%&'*+/=?^`{|}~\.-]{1,64}@[a-zA-Z0-9.-]{1,255}\.[a-zA-Z]{2,}$"
    # Check if the email address matches the pattern
    return regexmatch(pattern, email) is not None


def is_valid_pncd(pincode):
    """
    Check whether a pincode is valid.

    Args:
        pincode (str): The pincode to be checked.

    Returns:
        bool: True if the pincode is valid, False otherwise.
    """
    # Pattern to match a valid pincode
    pattern = r"^[1-9][0-9]{5}$"
    # Check if the pincode matches the pattern
    return regexmatch(pattern, pincode) is not None


def bill_num_formatr(bill_type, bill_timestamp, bill_num):
    """
    Format the bill number based on the bill type, timestamp, and bill number.

    Parameters:
        bill_type (str): The type of the bill. Valid values are "Invoice" or "EST".
        bill_timestamp (str): The timestamp of the bill in the format "YYYY-MM-DD".
        bill_num (int): The bill number.

    Returns:
        str: The formatted bill number in the format "BILL_TYPE-YEAR-MONTH-NUMBER".
    """
    # Extract the month and year from the bill timestam
    bill_month = int(bill_timestamp[5:7])
    bill_year = int(bill_timestamp[2:4])
    # Calculate the current bill year range
    bill_year = (
        f"{bill_year}/{bill_year + 1}"
        if bill_month > 3
        else f"{bill_year - 1}/{bill_year}"
    )
    # Determine the current bill type
    bill_type = "INV" if bill_type == "Invoice" else "EST"
    # Format and return the bill number with the bill type, year, month, and number
    return f"{bill_type}-{bill_year}-{str(bill_month).zfill(2)}-{str(bill_num).zfill(6)}"


def get_or_insert_ben(db, select_query, select_params, insert_query, insert_params):
    """
    Retrieves a record from the database using the provided select query and parameters.
    If the record exists, the corresponding "id" value is returned.
    If the record does not exist, a new record is inserted into the database using the insert query and parameters,
    and the newly inserted "id" value is returned.

    Parameters:
    - db: The database connection object.
    - select_query: The query to select a record from the database.
    - select_params: The parameters for the select query.
    - insert_query: The query to insert a new record into the database.
    - insert_params: The parameters for the insert query.

    Returns:
    - The "id" value of the retrieved or newly inserted record.
    - If an exception occurs during the execution of the queries, the exception object is returned.
    """
    try:
        # Execute the select query with the select parameters
        ben_id_db = db.execute(select_query, *select_params)

        # If the select query returned a record, return the corresponding "id" value
        # Otherwise, execute the insert query with the insert parameters and return the newly inserted "id" value
        ben_id = (
            ben_id_db[0]["id"]
            if ben_id_db
            else db.execute(insert_query, *insert_params)
        )
    except Exception as e:
        # If an exception occurs during the execution of the queries, return the exception object
        return e

    # Return the retrieved or newly inserted "id" value
    return ben_id


def handle_error(e):
    """
    A function that handles errors. It takes in an error object as a parameter.
    The error message is constructed using the type of the error and the error's arguments.
    The constructed error message is then passed to the render_template function along with
    an HTTP status code of 500. The function returns the rendered message template and the
    HTTP status code.

    Parameters:
    - e (Exception): The error object.

    Returns:
    - tuple: A tuple containing the rendered message template and the HTTP status code.
    """
    # Construct the error message using the type of the error and the error's arguments
    message = f"Something went wrong, please try again.\nError-code: INV-BEN-{type(e).__name__}.\nDEV-INFO: {e.args}"
    # Return the rendered message template and the HTTP status code
    return render_template("message.html", message=message), 500
