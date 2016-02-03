# -*- coding: utf-8 -*-
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse, Http404
from django.core.urlresolvers import reverse

from django.contrib.auth import authenticate, login,logout
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required

from importlib import import_module
from django.conf import settings
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
session = SessionStore()

from django.core import serializers
import json

from exam.models import *
from .forms import *

def home(request):
	request.session['rechargeError']=None
	request.session['qsetError']=None
	if request.user.is_authenticated():
		return redirect(reverse('dashboard', args=(request.user.id,)))

	context = {
		"title":"Home"
	}
	return render(request,'home.html',context)

def about(request):
	context = {
		'title': 'About Us',
	}
	return render(request, 'about.html', context)
def classes(request):
	context={
		"title":"Classes"
	}
	return render(request,'classes.html',context)

def faq(request):
	faq = Faq.objects.all()
	context={
		"title":"FAQ",
		'faq': faq,
	}
	return render(request,'faq.html',context)

def contactus(request):
	if request.method == 'POST':
		name = request.POST['name']
		email = request.POST['email']
		message = request.POST['message']

		contactus = ContactUs.objects.create(name=name, email=email, message=message)
		contactus.save()
	context={
		'title':'Contact Us',
	}
	return render(request, 'contact.html',context)

def doctor(request):
	news = News.objects.filter(faculty__exact='D')[:5]
	context = {
		'title':'Doctor',
		'news':news
	}
	return render(request,'news.html',context)

def engineer(request):
	news = News.objects.filter(faculty__exact='E')[:5]
	context = {
		'title':'Engineer',
		'news':news
	}
	return render(request,'news.html',context)

def register(request):
	if request.method == 'POST':
		userform = UserForm(request.POST)
		profileform = UserProfileForm(request.POST)
		if userform.is_valid() and profileform.is_valid():
			user = userform.save(commit=False)
			user.set_password(userform.cleaned_data['password'])
			user.save()
			userprofile = profileform.save(commit=False)
			userprofile.user = user
			userprofile.save()
			context={
				'title':'Register',
				"register":'Register Success'
			}
			return render(request,'register.html',context)
		context={
			'title':'Register',
			"userForm":userform,
			"userProfileForm":profileform,
			"register": 'Register Here'
		}
	else:
		userForm = UserForm()
		userProfileForm = UserProfileForm()
		context={
			'title':'Register',
			"userForm":userForm,
			"userProfileForm": userProfileForm,
			"register": 'Register Here'
		}
	return render(request,'register.html',context)

def login_view(request):
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		print request.POST
		user = authenticate(username=username, password=password)
		if user:
			if user.is_active:
				login(request, user)
				context={
					'title':'Login',
					'login':'Login Success',
				}
				print user.id
				return redirect(reverse('dashboard' , args=(user.id,)))
		else:
			context={
				'title':'Login',
				'login':'Login Here',
				'error':'Username or Password Invalid',
			}

	else:
		context={
			'title':'Login',
			'login':'Login Here',
		}
	return render(request,'login.html',context)

@login_required(login_url='login')
def logout_view(request):
	logout(request)
	return redirect(reverse('home'))

@login_required(login_url='login')
def dashboard(request, id):
	user = get_object_or_404(User,pk=id)
	if request.user == user:
		ioe_questionset = request.user.userquestionset_set.filter(qgroup='IOE').order_by('questionset')
		iom_questionset = request.user.userquestionset_set.filter(qgroup='IOM').order_by('questionset')
		moe_questionset = request.user.userquestionset_set.filter(qgroup='MOE').order_by('questionset')

		print len(ioe_questionset)
		context={
			'title':'Dashboard',
			'rechargeError': request.session['rechargeError'],
			'qsetError': request.session['qsetError'],
			'ioe_questionset':ioe_questionset,
			'iom_questionset':iom_questionset,
			'moe_questionset':moe_questionset,
			'firstname':user.first_name,

		}
		request.session['rechargeError']=None
		request.session['qsetError']=None
		return render(request,'dashboard.html',context)
	else:
		return redirect(reverse('home'))

@login_required(login_url='login')
def recharge(request):
	if request.method=='POST':
		group = request.POST['group']
		pin = request.POST['pin']
		user = request.user;
		key = Key.objects.filter(group=group,key=pin,status=False)
		
		print key
		if  not key:
			request.session['rechargeError']='Key is invalid'
			# print request.session['rechargeError']
		else:
			qset = user.userquestionset_set.filter(qgroup=group).count()
			for i in range(1,11):
				userquestionset=UserQuestionSet.objects.create(user=user,qgroup=group,questionset=qset+i)
				userquestionset.save()
			key[0].status=True
			key[0].save()


	return redirect(reverse('dashboard', args=(request.user.id,)))
@login_required(login_url='login')
def questionset(request,qgroup,qset):
	if qgroup.strip() == 'IOE':
		if len(request.user.userquestionset_set.filter(qgroup='IOE',questionset=qset,status=False))>0:
			english_question = QuestionIOE.objects.filter(questionset=qset).order_by('questionno')
			first_group = english_question[:10]
			second_group = english_question[10:20] 
			context={
				'first_group':first_group,
				'second_group':second_group,
				'qgroup':qgroup,
				'qset':qset,
			}
			return render(request,'questionset.html',context)
		else:
			request.session['qsetError']="You don't have acces to this question"
			return redirect(reverse('dashboard' ,args=(request.user.id,)))
	if qgroup.strip() == 'IOM':
		if(len(request.user.userquestionset_set.filter(qgroup='IOM',questionset=qset,status=False))>0):
			print qgroup,qset
			return HttpResponse("Your group is "+qgroup+" and questionset is "+qset)
		else:
			request.session['qsetError']="You don't have acces to this question"
			return redirect(reverse('dashboard' ,args=(request.user.id,)))
	if qgroup.strip() == 'MOE':
		if(len(request.user.userquestionset_set.filter(qgroup='MOE',questionset=qset,status=False))>0):
			print qgroup,qset
			return HttpResponse("Your group is "+qgroup+" and questionset is "+qset)
		else:
			request.session['qsetError']="You don't have acces to this question"
			return redirect(reverse('dashboard' ,args=(request.user.id,)))

@login_required(login_url='login')
def checkset(request, qgroup, qset):
	wrong=[]
	score={
		'english':0,
		'math':0,
		'total':0,
		'qgroup': qgroup,
	}
	if request.method == 'POST':
		print request.POST
		
		if qgroup == 'IOE':
			questionIOE = QuestionIOE.objects.filter(questionset=qset).order_by('questionno')
			for i in range(1,20):
				if i<=10:
					try:
						if request.POST[str(i)] == questionIOE[i-1].answer:
							score['english'] +=1
							score['total'] +=1
							
						else:
							wrong.append(i-1)
					except Exception as ex:
						pass

				elif i<=20:
					try:
						if request.POST[str(i)] == questionIOE[i-1].answer:
							score['math'] +=1
							score['total'] +=1
						else:
							wrong.append(i-1)
					except Exception as ex:
						pass
				else:
					pass
		
			wrong_questions = []
			for questionno in wrong:
				wrong_questions.append(questionIOE[questionno])
		elif qgroup == 'IOM':
			for questionno in wrong:
				question = QuestionIOM.objects.filter(questionset=qset,questionno=questionno)
				wrong_questions.append(question)
		elif qgroup == 'MOE':
			for questionno in wrong:
				question = QuestionMOE.objects.filter(questionset=qset,questionno=questionno)
				wrong_questions.append(question)
		else:
			pass
		score['wrong_questions']=wrong_questions
		# score = json.dumps(score)
		return render(request, 'result.html', score)
					

	else:
		return redirect(reverse('dashboard', args=(request.user.id,) ))

@login_required(login_url='login')
def rules(request, qgroup, qset):
	if qgroup=='IOE':
		context={
			'title':'Rules',
			'firstname':request.user.first_name,
			'qgroup': qgroup,
			'qset':qset,

		}
		return render(request,'rules_ioe.html', context)
	if qgroup=='IOM':
		context={
			'title':'Rules',
			'firstname':request.user.first_name,
			'qgroup': qgroup,
			'qset':qset,

		}
		return render(request,'rules_iom.html', context)
	if qgroup=='MOE':
		context={
			'title':'Rules',
			'firstname':request.user.first_name,
			'qgroup': qgroup,
			'qset':qset,

		}
		return render(request,'rules_moe.html', context)

#######################api#################

def api_questions(request,qgroup,qset):
	if qgroup=='ioe':
		questions = QuestionIOE.objects.filter(questionset=qset).order_by('questionno')[:5]
		# questionno = serializers.serialize("json", questions, fields=('question',))
		question_set = []
		# print questionno
		
		for question in questions:
			answers = question.answerioe_set.all()
			answer_set=[]
			# answer = serializers.serialize("json", answers, fields=('answer','value'))
			for answer in answers:
				answer_set.append({'answer':answer.answer,'value':answer.value})
			question_set.append({'question':question.question,'answer':answer_set})
		print question_set
		return HttpResponse(json.dumps(question_set))
	elif qgroup=='iom':
		return HttpResponse("Not done yet")
	elif qgroup=='moe':
		return HttpResponse("Not done yet")

	
