# zakat_utils.py

def calculate_zakat(camel_count):
    # Base cases up to 200 camels, following the exact table
    if camel_count <= 4:
        return "0 zakat"
    elif 5 <= camel_count <= 9:
        return "1 goat"
    elif 10 <= camel_count <= 14:
        return "2 goats"
    elif 15 <= camel_count <= 19:
        return "3 goats"
    elif 20 <= camel_count <= 24:
        return "4 goats"
    elif 25 <= camel_count <= 35:
        return "1 bint makhāḍ (1 y/o camel)"
    elif 36 <= camel_count <= 45:
        return "1 bint labūn (2 y/o camel)"
    elif 46 <= camel_count <= 60:
        return "1 ḥiqqah (3 y/o camel)"
    elif 61 <= camel_count <= 75:
        return "1 jadha'ah (4 y/o camel)"
    elif 76 <= camel_count <= 90:
        return "2 bint labūns (2 y/o camel)"
    elif 91 <= camel_count <= 120:
        return "2 ḥiqqahs (3 y/o camel)"
    elif 125 <= camel_count <= 129:
        return "1 goat + 2 ḥiqqahs (3 y/o camel)"
    elif 130 <= camel_count <= 134:
        return "2 goats + 2 ḥiqqahs (3 y/o camel)"
    elif 135 <= camel_count <= 139:
        return "3 goats + 2 ḥiqqahs (3 y/o camel)"
    elif 140 <= camel_count <= 144:
        return "4 goats + 2 ḥiqqahs (3 y/o camel)"
    elif 145 <= camel_count <= 149:
        return "1 bint makhāḍ (1 y/o camel) + 2 ḥiqqahs (3 y/o camel)"
    elif 150 <= camel_count <= 154:
        return "3 ḥiqqahs (3 y/o camel)"
    elif 155 <= camel_count <= 159:
        return "1 goat + 3 ḥiqqahs (3 y/o camel)"
    elif 160 <= camel_count <= 164:
        return "2 goats + 3 ḥiqqahs (3 y/o camel)"
    elif 165 <= camel_count <= 169:
        return "3 goats + 3 ḥiqqahs (3 y/o camel)"
    elif 170 <= camel_count <= 174:
        return "4 goats + 3 ḥiqqahs (3 y/o camel)"
    elif 175 <= camel_count <= 185:
        return "1 bint makhāḍ (1 y/o camel) + 3 ḥiqqahs (3 y/o camel)"
    elif 186 <= camel_count <= 195:
        return "1 bint labūn (2 y/o camel) + 3 ḥiqqahs (3 y/o camel)"
    elif 196 <= camel_count <= 200:
        return "4 ḥiqqahs (3 y/o camel)"
    
    # For camels greater than 200, repeat the pattern with additional ḥiqqahs every 50 camels
    elif camel_count > 200:
        additional_cycles = (camel_count - 200) // 50
        base_zakat = f"{4 + additional_cycles} ḥiqqahs (3 y/o camel)"
        cycle_position = (camel_count - 150) % 50
        
        if cycle_position <= 4:
            return base_zakat
        elif 5 <= cycle_position <= 9:
            return f"{base_zakat} + 1 goat"
        elif 10 <= cycle_position <= 14:
            return f"{base_zakat} + 2 goats"
        elif 15 <= cycle_position <= 19:
            return f"{base_zakat} + 3 goats"
        elif 20 <= cycle_position <= 24:
            return f"{base_zakat} + 4 goats"
        elif 25 <= cycle_position <= 35:
            return f"{base_zakat} + 1 bint makhāḍ (1 y/o camel)"
        elif 36 <= cycle_position <= 45:
            return f"{base_zakat} + 1 bint labūn (2 y/o camel)"
        else:
            return base_zakat
    else:
        return "Invalid input"

