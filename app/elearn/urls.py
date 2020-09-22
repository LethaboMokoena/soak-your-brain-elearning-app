from django.urls import path

from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('signup/', home, name='signup'),
    path('signup/<str:plan_subscribed>', sign_up, name='signup'),
    path('signin/', sign_in, name='signin'),
    path('signout/', sign_out, name='signout'),
    path('checkout/', checkout_page, name='checkout_page'),
    path('sybadmin/', syb_admin_page, name='syb_admin_page'),
    path('college/', college_page, name='college_page'),
    path('college/add_teachers', college_add_teachers, name='college_add_teachers'),
    path('college/add_teachers/<int:pk>', college_add_teachers, name='college_add_teachers'),
    path('college/del_teachers/<int:pk>', college_del_teachers, name='college_del_teachers'),
    path('college/add_classes', college_add_classes, name='college_add_classes'),
    path('college/add_classes/<int:pk>', college_add_classes, name='college_add_classes'),
    path('college/del_classes/<int:pk>', college_del_classes, name='college_del_classes'),
    path('college/teacher', college_teacher, name='college_teacher'),
    path('college/teacher/add_subjects', college_teacher_add_subjects, name='college_teacher_add_subjects'),
    path('college/teacher/add_subjects/<int:pk>', college_teacher_add_subjects, name='college_teacher_add_subjects'),
    path('college/teacher/add_students', college_teacher_add_students, name='college_teacher_add_students'),
    path('college/teacher/add_students/<int:pk>', college_teacher_add_students, name='college_teacher_add_students'),
    path('college/teacher/classroom/<int:pk>', college_teacher_classroom, name='college_teacher_classroom'),
    path('college/student', college_student, name='college_student'),
]
