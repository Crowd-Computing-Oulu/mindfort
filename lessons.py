
import json

# Load lessons from JSON file
with open('lessons.json', 'r') as f:
    lessons = json.load(f)
            
def get_lessons_number():
    return len(lessons)

def get_lesson_by_id_with_ordering(id, lessons_order):
    # print(lessons_order.split(','))
    # print(id)
    # print(int(lessons_order.split(',')[id]))
    # print(lessons[int(lessons_order.split(',')[id])])
    lesson = lessons[int(lessons_order.split(',')[id])]
    lesson['id'] = id
    return lesson

def get_lesson_by_id(id):
    return lessons[id]
                        