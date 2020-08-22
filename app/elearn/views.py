import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .decorators import unauthenticated_user, allowed_users
from .models import *


# Views and endpoints
def home(request):
    context_dict = {}
    return render(request, template_name='home.html', context=context_dict)


@unauthenticated_user
def sign_up(request, plan_subscribed=''):
    if request.method == 'POST':
        data = json.loads(request.body)
        first_name = data['first_name']
        last_name = data['last_name']
        college_name = data['college_name']
        email_id = data['email_id']
        password1 = data['password']
        phone_no = data['phone_no']
        card_no = data['card_no']
        card_cvv = data['card_cvv']
        plan_subscribed = data['plan_subscribed']

        # Process payment
        # This is just dummy code because I am not going to implement any actual
        # payment processing for this project
        pay_status_failed = False
        if pay_status_failed:
            return redirect(payment_failed)

        try:
            # register the User
            new_user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email_id,
                username=email_id,
            )
            new_user.set_password(password1)
            new_user.save()

            # Add this user to collegeadmin group
            collegeadmin_group = Group.objects.get(name='collegeadmin')
            collegeadmin_group.user_set.add(new_user)

            # get the plan_subscribed object
            plan = Plan.objects.get(name=plan_subscribed)
            plan.save()

            # register the User as College
            college = College.objects.create(
                user=new_user,
                plan_subscribed=plan,
                first_name=first_name,
                last_name=last_name,
                college_name=college_name,
                email=email_id,
                phone_no=phone_no,
                card_info=card_no,
            )
            college.save()

            # now at last the College as Customer
            customer = Customer.objects.create(
                user=new_user,
                plan_subscribed=plan,
                first_name=first_name,
                last_name=last_name,
                college_name=college_name,
                email=email_id,
                phone_no=phone_no,
            )
            customer.save()

            # Now log the user in
            auth_user = authenticate(request, username=email_id, password=password1)
            if auth_user is not None:
                login(request, auth_user)
                return redirect(college_page)
            else:
                return JsonResponse({'process': 'failed', 'error': 'User authentication system failed'})
        except IntegrityError:
            return JsonResponse({'process': 'failed', 'error': 'User already exists'})
        except Exception as err:
            return JsonResponse({'process': 'failed', 'error': f'{str(err)}'})
    plans = Plan.objects.all().values_list('name', flat=True)
    if plan_subscribed not in plans:
        return render(request, template_name='home.html')
    cost_of_selected_plan = Plan.objects.get(name=plan_subscribed).price_per_year
    context_dict = {'plan_selected': plan_subscribed, 'plan_cost': f'₹{int(cost_of_selected_plan)} / year'}
    return render(request, template_name='sign_up.html', context=context_dict)


@unauthenticated_user
def sign_in(request):
    if request.method == 'POST':
        username = request.POST.get('email')  # username and email are one and the same
        password = request.POST.get('password')
        try:
            # Log the user in
            auth_user = authenticate(request, username=username, password=password)
            if auth_user is not None:
                login(request, auth_user)
                # Now redirect based on what group user is a part of
                login_user = User.objects.get(username=username)
                login_user_group = login_user.groups.all()[0].name
                redirect_dict = {
                    'collegeadmin': college_page,
                    'teacher': college_teacher,
                    'student': college_student,
                    'sybadmin': syb_admin_page,
                }
                return redirect(redirect_dict[login_user_group])
            else:
                if User.objects.filter(username=username).exists():
                    context_dict = {'msg': 'Email id or password is wrong'}
                    return render(request, template_name='sign_in.html', context=context_dict)
                else:
                    context_dict = {'msg': 'User does not exist please sign up first'}
                    return render(request, template_name='sign_in.html', context=context_dict)
        except Exception as e:
            context_dict = {'msg': 'Email id or password is wrong'}
            return render(request, template_name='sign_in.html', context=context_dict)
    context_dict = {}
    return render(request, template_name='sign_in.html', context=context_dict)


def sign_out(request):
    # sign out logic here
    logout(request)
    context_dict = {'msg': 'Logged out successfully'}
    return render(request, template_name='sign_in.html', context=context_dict)


def checkout_page(request):
    context_dict = {}
    return render(request, template_name='checkout/checkbout.html', context=context_dict)


@login_required
@allowed_users(allowed_roles=['sybadmin'])
def syb_admin_page(request):
    context_dict = {}
    return render(request, template_name='sybadmin/dashboard/dashboard.html', context=context_dict)


@login_required
@allowed_users(allowed_roles=['collegeadmin'])
def college_page(request):
    teachers = Teacher.objects.all()
    departments = Department.objects.all()
    classes = CollegeClass.objects.all()
    context_dict = {
        'teachers': teachers,
        'departments': departments,
        'classes': classes,
    }
    return render(request, template_name='college/admin/college_admin.html', context=context_dict)


@login_required
@allowed_users(allowed_roles=['collegeadmin'])
def college_add_teachers(request, pk=None):
    classes_list = [classname['name'] for classname in CollegeClass.objects.all().values('name')]
    if request.method == 'POST':
        # for AJAX request
        data = json.loads(request.body)
        mode = data['mode']
        first_name = data['first_name']
        last_name = data['last_name']
        classes_assigned = data['classes_assigned']
        email_id = data['email_id']
        password1 = None if data['password1'] == '' else data['password1']

        if mode == 'add':
            # request is for adding new teacher
            try:
                # register the User
                new_user = User.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    email=email_id,
                    username=email_id,
                )
                new_user.set_password(password1)
                new_user.save()

                # Add this user to teacher group
                collegeadmin_group = Group.objects.get(name='teacher')
                collegeadmin_group.user_set.add(new_user)

                # Get the college of the current logged in user (collegeadmin user)
                college = request.user.college

                # create a teacher
                clg_teacher = Teacher.objects.create(
                    user=new_user,
                    college=college,
                    first_name=first_name,
                    last_name=last_name,
                    email=email_id,
                )

                # add the assigned classes to this teacher
                for cls in classes_assigned:
                    clg_cls = CollegeClass.objects.get(name=cls)
                    clg_teacher.college_classes.add(clg_cls)

                return JsonResponse({
                    'process': 'success',
                    'msg': f'Success! Teacher {first_name} {last_name} has been added to the database.',
                })
            except IntegrityError:
                return JsonResponse({
                    'process': 'failed',
                    'msg': f'Teacher {first_name} {last_name} has already been added to the database.'
                })
            except Exception as err:
                return JsonResponse({'process': 'failed', 'msg': f'{err}'})
        else:
            # this is an AJAX request for updating existing teacher
            # This request also will contain password2 field data as password validation is
            # not done on client side for this request's form
            password2 = None if data['password2'] == '' else data['password2']
            try:
                # Get the teacher by pk (id) and update the data
                clg_teacher_id = data['teacher_id']
                clg_teacher = Teacher.objects.get(pk=clg_teacher_id)
                clg_teacher.first_name = first_name
                clg_teacher.last_name = last_name
                clg_teacher.email = email_id

                # Now update the User associated (OneToOne) with the Teacher
                clg_teacher.user.email = email_id
                clg_teacher.user.username = email_id
                clg_teacher.user.first_name = first_name
                clg_teacher.user.last_name = last_name

                # Update the classes assigned to the teacher
                # First clear existing classes data
                clg_teacher.college_classes.clear()
                # Now add newly selected/edited data
                for cls in classes_assigned:
                    clg_cls = CollegeClass.objects.get(name=cls)
                    clg_teacher.college_classes.add(clg_cls)

                # if the password provided is valid then update it too
                if password1 is not None and password2 is not None:
                    if password1 == password2:
                        clg_teacher.user.set_password(password1)
                    else:
                        return JsonResponse({
                            'process': 'failed',
                            'msg': f'Error! passwords do not match',
                        })

                # Now save the data
                clg_teacher.user.save()
                clg_teacher.save()

                # updated_teacher_data is for updating the html table in the frontend once
                # request gets processed
                updated_teacher_data = {
                    'id': clg_teacher.id,
                    'first_name': clg_teacher.first_name,
                    'last_name': clg_teacher.last_name,
                    'email_id': clg_teacher.email,
                    'class_list': [cls_name.name for cls_name in clg_teacher.college_classes.all()],
                }

                # Return success message
                return JsonResponse({
                    'process': 'success',
                    'msg': f'{first_name} {last_name}\'s data has been successfully updated.',
                    'updated_data': updated_teacher_data,
                })
            except Exception as err:
                return JsonResponse({
                    'process': 'failed',
                    'msg': f'Error! {err}',
                })
    if pk is not None:
        # it means that this is an AJAX GET request for getting a teacher's data using pk (id)
        try:
            teacher = Teacher.objects.get(pk=pk)
            teacher_json_obj = {
                'first_name': teacher.first_name,
                'last_name': teacher.last_name,
                'classes_assigned': [teach.name for teach in teacher.college_classes.all()],
                'email_id': teacher.email,
            }
            return JsonResponse({
                'process': 'success',
                'msg': 'Success',
                'teacher_json_obj': teacher_json_obj,
            })
        except Exception as err:
            return JsonResponse({
                'process': 'failed',
                'msg': f'Error! {err}',
            })

    context_dict = {'classes_list': classes_list}
    return render(request, template_name='college/admin/admin_addteachers.html', context=context_dict)


@login_required
@allowed_users(allowed_roles=['collegeadmin'])
def college_add_classes(request, pk=None):
    departments_list = [department['name'] for department in Department.objects.all().values('name')]
    if request.method == 'POST':
        # for AJAX request
        data = json.loads(request.body)
        form_type = data['form_type']
        if form_type == 'department':
            if pk is None:
                # this means that the request came from 'add new department' form
                department_name = data['department_name']
                college = request.user.college
                try:
                    Department.objects.get_or_create(
                        college=college,
                        name=department_name,
                    )
                    return JsonResponse({
                        'process': 'success',
                        'msg': f'Success! {department_name} department added to the database.',
                        'departments_list': departments_list,
                    })
                except IntegrityError:
                    return JsonResponse({'process': 'failed', 'msg': f'{department_name} already exists.'})
                except Exception as err:
                    return JsonResponse({'process': 'failed', 'msg': f'{err}'})
            else:
                # this request came for updating an existing department's fields
                department_name = data['department_name']
                try:
                    dep = Department.objects.get(pk=pk)
                    dep.name = department_name
                    dep.save()

                    return JsonResponse({
                        'process': 'success',
                        'department_name': f'{dep.name}',
                    })
                except IntegrityError:
                    return JsonResponse({
                        'process': 'failed',
                        'msg': 'Duplicate value error',
                    })
                except Exception as err:
                    return JsonResponse({
                        'process': 'failed',
                        'msg': f'{err}',
                    })
        elif form_type == 'class':
            if pk is None:
                # this means that the request came from 'add new classes' form
                class_name = data['class_name']
                department = Department.objects.get(name=data['department_name'])
                college = request.user.college
                try:
                    CollegeClass.objects.create(
                        college=college,
                        name=class_name,
                        department=department,
                    )
                    return JsonResponse({
                        'process': 'success',
                        'msg': f'Success! {class_name} class added in {department.name}',
                        'departments_list': departments_list,
                    })
                except IntegrityError:
                    return JsonResponse({'process': 'failed',
                                         'msg': f'{class_name} already exists in {department.name} department.'})
                except Exception as err:
                    return JsonResponse({'process': 'failed', 'msg': f'{err}'})
            else:
                # this request came for updating an existing class's fields
                class_name = data['class_name']
                department_name = data['department_name']
                try:
                    cls = CollegeClass.objects.get(pk=pk)
                    cls.name = class_name
                    cls.department = Department.objects.get(name=department_name)
                    cls.save()

                    return JsonResponse({
                        'process': 'success',
                        'class_name': f'{cls.name}',
                        'department_name': f'{cls.department}',
                    })
                except IntegrityError:
                    return JsonResponse({
                        'process': 'failed',
                        'msg': 'Duplicate value error',
                    })
                except Exception as err:
                    return JsonResponse({
                        'process': 'failed',
                        'msg': f'{err}',
                    })
    context_dict = {
        'departments_list': departments_list,
    }
    return render(request, template_name='college/admin/admin_addclasses.html', context=context_dict)


@login_required
@allowed_users(allowed_roles=['teacher'])
def college_teacher(request):
    context_dict = {}
    return render(request, template_name='college/teacher/teacher.html', context=context_dict)


@login_required
@allowed_users(allowed_roles=['student'])
def college_student(request):
    context_dict = {}
    return render(request, template_name='college/student/student.html', context=context_dict)


def payment_failed(request):
    return render(request, template_name='payment_failed.html')
