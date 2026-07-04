import os
import re

txt_path = os.path.join(os.path.dirname(__file__), "..", "HORARIOSCOMPLETOSUPAO.txt")

with open(txt_path, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f.readlines()]

i = 0
current_cycle = 1

while i < len(lines):
    line = lines[i]
    if not line:
        i += 1
        continue
        
    if "ciclo" in line.lower() and len(line) < 15:
        match = re.search(r'(\d+)', line)
        if match:
            current_cycle = int(match.group(1))
        i += 1
        continue
        
    if "NRC:" in line:
        # We are probably inside a section block, backtrack to find course name
        # The course info is 2 lines above NRC: if "PRESENCIAL" is 1 line above
        if "PRESENCIAL" in lines[i-1].upper() or "VIRTUAL" in lines[i-1].upper():
            course_line = lines[i-2]
            # Format: ICSI - ( CIEN-752 ) ALGEBRA MATRIC Y GEOM ANALIT
            m_course = re.search(r'\(\s*([\w\-]+)\s*\)\s*(.*)', course_line)
            if m_course:
                course_code = m_course.group(1).strip()
                course_name = m_course.group(2).strip()
                
                nrc = lines[i+1].strip()
                secc_header = lines[i+2]
                secc = lines[i+3].strip()
                
                print(f"Cycle: {current_cycle} | Code: {course_code} | Name: {course_name} | NRC: {nrc} | SECC: {secc}")
                
        # Skip this block to not print 1000 times
        i += 4
        continue
        
    i += 1
    
    if i > 500: break
