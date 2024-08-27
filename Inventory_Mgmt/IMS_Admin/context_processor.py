from .models import Employee  # Import the Employee model

def session_data(request):
    """
    Custom context processor to pass session data including userid, username, email, 
    department, and mobile number to all templates.
    Returns these values from the session if the user is logged in, otherwise returns None.
    """
    user_data = {
        'userid': None,
        'username': None,
        'emailid': None,
        'department': None,
        'phone_number': None,
        'first_name': None,  # Adding first name separately for your use in templates
    }
    
    if 'userid' in request.session:
        try:
            # Fetch the employee details from the database
            employee = Employee.objects.get(id=request.session.get('userid'))
            user_data['userid'] = employee.id
            user_data['username'] = f"{employee.First_name} {employee.last_name}"
            user_data['emailid'] = employee.email
            user_data['department'] = employee.department.name if employee.department else None
            user_data['phone_number'] = employee.phone_number
            user_data['first_name'] = employee.First_name
        except Employee.DoesNotExist:
            # If the employee is not found in the database, clear the session data
            request.session.flush()

    return {'emp': user_data}
