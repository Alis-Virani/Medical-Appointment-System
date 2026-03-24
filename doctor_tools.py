# tools.py
# ---------------------------------------------------------
# This tool handles the connection between the Agent and the Database.
# ---------------------------------------------------------
from database import find_doctors_in_db

def get_doctors_tool(specialty: str, city: str):
    """
    Retrieves a list of doctors based on specialty and city.
    """
    # If the user didn't specify a city, default to "Jamnagar"
    if not city:
        city = "Jamnagar" 
        
    results = find_doctors_in_db(specialty, city)
    
    if not results:
        return None
    
    doctors_list = []
    for doc in results:
        doctors_list.append({
            "name": doc[0],
            "specialty": doc[1],
            "time": doc[2],
            "city": doc[3]
        })
    return doctors_list