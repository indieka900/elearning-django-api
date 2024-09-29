from django.contrib import admin
from elearning.models import (
    Course, CourseModule, CourseProfile, Enrollment, Lesson, 


    LessonAssignment, LessonProgress, LiveClassSchedule, ModuleAssignment,
    ModuleProgress, UserProgress, UserActivity,AssignmentSubmission, Assignment, SubscriptionPlan


)

admin.site.register(Course)
admin.site.register(LiveClassSchedule)
admin.site.register(CourseProfile)
admin.site.register(CourseModule)
admin.site.register(Lesson)
admin.site.register(Enrollment)
admin.site.register(ModuleProgress)
admin.site.register(LessonProgress)
admin.site.register(ModuleAssignment)
admin.site.register(LessonAssignment)
admin.site.register(AssignmentSubmission)
admin.site.register(Assignment)
admin.site.register(UserActivity)
admin.site.register(UserProgress)
admin.site.register(SubscriptionPlan)
