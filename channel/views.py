from django.shortcuts import render, redirect
import datetime
from .models import *
import requests,arrow
from django.contrib.auth import authenticate, login as auth_login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.db.models.fields.related import ManyToManyField
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
import os
from django.conf import settings
from django.http import HttpResponse

def to_dict(instance):
    opts = instance._meta
    data = {}
    for f in opts.concrete_fields + opts.many_to_many:
        if isinstance(f, ManyToManyField):
            if instance.pk is None:
                data[f.name] = []
            else:
                data[f.name] = list(f.value_from_object(instance).values_list('pk', flat=True))
        else:
            data[f.name] = f.value_from_object(instance)
    return data



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def index(request):
	user=request.user
	chan = Channel.objects.all()
	Channels_all=[]
	for each in chan:
		data = to_dict(each)
		try:
			subs = Subscription.objects.get(c_id=data['c_id'],u_id=user)
			data['subs'] = True
		except:
			data['subs'] = False
		Channels_all.append(data)
	Channels_all=sorted(Channels_all,key=lambda d:-d['no_of_subscriptions'])

	return render(request,'archile/index.html',{'channels':Channels_all})



def user_login(request):
	return render(request,'archile/login.html')

#user logout
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return redirect(login)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def search(request,query):
	
	def valid_date(inputDate):
		try:
			year,month,day = inputDate.split('-')
		except:
			return False

		isValidDate = True

		try :
		    datetime.datetime(int(year),int(month),int(day))
		except ValueError :
		    isValidDate = False
		
		return isValidDate
	
	def valid_search(search_query):
		if 'search_query' not in search_query:
			return False
		if 'from' in search_query:
			if valid_date(search_query['from']) == False:
				return False
		if 'to' in search_query:
			if valid_date(search_query['to']) == False:
				return False

		for i in ['channel','post','documents','videos','images','audio','archives']:
			if i in search_query:
				if search_query[i] != 'on':
					return False
		
		if 'sort' in search_query:
			if search_query['sort'] not in ['uploadDate_asc','uploadDate_dec','likes_asc','likes_dec','size_asc','size_dec']:
				return False
		return True

	#query is a string, converting it to dictionary
	user=request.user
	query = eval(query)

	if valid_search(query):
		#Send the search reults with this query to search-results page.
		text =query['search_query'].lower().split()
		
		Channels = Channel.objects.all()
		Posts = Post.objects.all()
		Ch=[]
		Ps=[]
		for word in text:
			Ch.append(Channels.filter(name__icontains=word))
			Ps.append(Posts.filter(title__icontains=word))
		Channels_all=[]
		ch_set = set()
		for chan in Ch:
			for each in chan:
				if each.c_id not in ch_set:
					data = to_dict(each)
					try:
						subs = Subscription.objects.get(c_id=data['c_id'],u_id=user)
						data['subs'] = True
					except:
						data['subs'] = False
					ch_set.add(data['c_id'])
					Channels_all.append(data)
		Channels_all=sorted(Channels_all,key=lambda d:-d['no_of_subscriptions'])
		Posts_all=[]
		ps_set = set()
		for pst in Ps:
			for each in pst:
				if each.p_id not in ps_set:
					data = to_dict(each)
					ps_set.add(data['p_id'])
					Posts_all.append(data)
		Posts_all=sorted(Posts_all,key=lambda d:[-d['no_of_likes'],d['no_of_dislikes'],d['creation_datetime']])
		context = {
			'channels': Channels_all,
			'posts': Posts_all
		}
		return render(request, 'archile/search_results.html',context)
	else:
		# redirect to home page, as of now redirecting to search_box(which is a dummy for our search filter)
		return redirect(search_box)
	
	return render(request, 'archile/search.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def search_box(request):

	if request.method == 'POST':
		query = {}
		for i in request.POST:
			query[i] = request.POST[i]

		del query['csrfmiddlewaretoken']

		# if query['from'] == '':
		# 	del query['from']

		# if query['to'] == '':
		# 	del query['to']

		return redirect(search,query)


def home(request,token_id):
	payload = {'token': token_id, 'secret':"6d5fc80be2b62f1eb699f1be6bfc44394de1e2e18f7fd825a7cf045e9825b5ac2d5661b924965f49b97d6827a5bbd298e1549660d43ea70c5830af0241ff3482"}
	url = "https://serene-wildwood-35121.herokuapp.com/oauth/getDetails"
	response=requests.post(url, data=payload)
	data=response.json()
	#print(data)
	data=data['student']
	try:
		user_object = User.objects.get(email=data[0]['Student_Email'])
	except:
		user_object=User()
	user_object.first_name=data[0]['Student_First_Name']
	user_object.last_name=data[0]['Student_Last_name']
	user_object.email=data[0]['Student_Email']
	user_object.token=token_id
	user_object.is_active = True
	user_object.save()
	auth_login(request,user_object)
	return redirect(index)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def create_channel(request):
	if request.method == 'POST':
		name = request.POST['channel_name']
		if 'channel_logo' in request.FILES:
			logo = request.FILES['channel_logo']
		description = request.POST['channel_description']
		tags = list(map(lambda tag:tag.strip(),request.POST['channel_tags'].split(',')))
		user = request.user

		utc = arrow.utcnow()
		local = utc.to('Asia/Kolkata')
		channel_object = Channel(u_id=user,name=name,description=description,logo=logo,creation_datetime=local)
		channel_object.save()

		#saving all tags
		for tag in tags:
			try:
				tag_obj=Tags.objects.get(tag_name=tag)
				tag_obj.no_of_use+=1
			except:
				tag_obj = Tags(tag_name=tag,no_of_use = 1)
			tag_obj.save()
			channel_tag=Channel_tags(c_id=channel_object,t_id=tag_obj)
			channel_tag.save()
		return redirect(create_channel)
	return render(request, 'archile/create_channel.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def create_post(request,c_id):
	channel = Channel.objects.get(c_id=c_id)
	return render(request, 'archile/create_post.html',{'channel':channel})



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def save_post(request):
	if request.method == 'POST':
		user = request.user
		title = request.POST['post_title']
		c_id = request.POST['channel']
		ch = Channel.objects.get(c_id=c_id)
		description = request.POST['post_description']
		tags = list(map(lambda tag:tag.strip().lower(),request.POST['post_tags'].split(',')))

		#getting all files
		FILES = ['AUDIO','VIDEO','IMAGES','DOCS','ARCHIVES']
		file_data={}
		for file in FILES:
			if file in request.FILES:
				file_data[file] = request.FILES.getlist(file)

		utc = arrow.utcnow()
		local = utc.to('Asia/Kolkata')
		post_object = Post(u_id=user,c_id=ch,description=description,title=title,creation_datetime=local)
		post_object.save()

		#saving all tags
		for tag in tags:
			try:
				tag_obj=Tags.objects.get(tag_name=tag)
				tag_obj.no_of_use+=1
			except:
				tag_obj = Tags(tag_name=tag,no_of_use = 1)
			tag_obj.save()
			post_tag=Post_tags(p_id=post_object,t_id=tag_obj)
			post_tag.save()


		#saving all files
		for file_name in file_data:
			for file in file_data[file_name]:
				pf_obj=Post_files(p_id=post_object,file_type=file_name,file=file,upload_datetime=local)
				pf_obj.save()

		return redirect(channel,c_id)
	return render(request, 'archile/channel.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def edit_post(request,p_id):
	post_obj=Post.objects.get(p_id=p_id)
	post_tag_object = Post_tags.objects.filter(p_id=p_id)
	context = {'post':post_obj,'tags':post_tag_object}
	if request.method == 'POST':
		title = request.POST['post_title']
		description = request.POST['post_description']
		post_obj.title=title
		post_obj.description=description
		post_obj.save()
		files = request.POST.getlist('old_file')
		for pf_id in files:
			postf_obj=Post_files.objects.get(pf_id=pf_id)
			postf_obj.status=False
			print(postf_obj.file)
			postf_obj.save()
		post_tags = request.POST['post_tags']
		print(post_tags)
		utc = arrow.utcnow()
		local = utc.to('Asia/Kolkata')
		FILES = ['AUDIO','VIDEO','IMAGES','DOCS','ARCHIVES']
		file_data={}
		for file in FILES:
			if file in request.FILES:
				file_data[file] = request.FILES.getlist(file)
				
		for file_name in file_data:
			for file in file_data[file_name]:
				pf_obj=Post_files(p_id=post_obj,file_type=file_name,file=file,upload_datetime=local)
				pf_obj.save()

		return redirect(post,p_id)

	return render(request, 'archile/edit_post.html', context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def edit_channel(request,c_id):
	return redirect(channel,c_i)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')	
def subscribe_channel(request,c_id):
	Chan = Channel.objects.get(c_id=c_id)
	count =Chan.no_of_subscriptions
	user = request.user
	utc = arrow.utcnow()
	local = utc.to('Asia/Kolkata')
	try:
		subs = Subscription.objects.get(c_id=Chan,u_id=user)
		Chan.no_of_subscriptions = count -1
		subs.delete()
	except:
		subs = Subscription(c_id=Chan,u_id=user,s_datetime=local)
		if count == None:
			Chan.no_of_subscriptions = 1
		else:
			Chan.no_of_subscriptions = count + 1
		subs.save()
	Chan.save()
	return redirect(channel,c_id)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def post(request,p_id):
	post_obj = Post.objects.get(p_id=p_id)
	context={}
	context['post'] = post_obj
	files = Post_files.objects.filter(p_id=p_id)
	thread_obj = Post_threads.objects.filter(p_id=p_id,pt_id_reply_to=None)
	post_files = []
	post_threads = []
	for f in files:
		p=str(f.file)
		f.filename=p.split('/')[1]
		post_files.append(f)
	for thread in thread_obj:
		reply_threads = Post_threads.objects.filter(pt_id_reply_to=thread.pt_id)
		val = [thread,reply_threads]
		post_threads.append(val)
	context['post_files'] = post_files
	context['post_threads'] = post_threads
	return render(request, 'archile/post.html',context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def report_post(request, p_id):
	user = request.user
	try:
		post_act_obj = post_actions.objects.get(p_id = p_id,u_id=user)
		if post_act_obj.report_status == True:
			post_act_obj.report_status = False
		elif post_act_obj.report_status == False:
			post_act_obj.report_status = True
	except:
		post_act_obj = post_actions()
		post_act_obj.report_status = True
		post_act_obj.u_id=user
	post_act_obj.save()
	return redirect(post,p_id)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def channel(request,c_id):
	channel = Channel.objects.get(c_id=c_id)
	posts=Post.objects.filter(c_id=channel)
	user = request.user
	context = {}
	context['channel'] = channel
	context['posts']=[]
	context['docs']=[]
	context['images']=[]
	context['audio']=[]
	context['video']=[]
	context['archives']=[]
	for post in posts:
		post.creation_datetime=arrow.get(post.creation_datetime).format('Do MMMM YYYY')
		context['posts'].append(post)
		files=Post_files.objects.filter(p_id=post.p_id)
		for f in files:
			p=str(f.file)
			f.filename=p.split('/')[1]
			if f.file_type == "IMAGES":
				context['images'].append(f)
			if f.file_type == "AUDIO":
				context['audio'].append(f)
			if f.file_type == "VIDEO":
				context['video'].append(f)
			if f.file_type == "DOCS":
				context['docs'].append(f)
			if f.file_type == "ARCHIVES":
				context['archives'].append(f)
	try:
		subs = Subscription.objects.get(c_id=channel,u_id=user)
		context['subs'] = True
	except:
		context['subs'] = False
	return render(request, 'archile/channel.html',context)

	
def download(request, path):
	path='post_files/'+path
	file_path = os.path.join(settings.MEDIA_ROOT, path)
	if os.path.exists(file_path):
		with open(file_path, 'rb') as fh:
			response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
			response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
			return response
	raise Http404

def actions(request,type_of,action,any_id):
	utc = arrow.utcnow()
	local = utc.to('Asia/Kolkata')
	action = int(action)
	if type_of=='post':
		post_file_obj=Post.objects.get(p_id=any_id)
	elif type_of=='post_file':
		post_file_obj=Post_files.objects.get(pf_id=any_id)
	try:
		if type_of=='post':
			action_object=post_actions.objects.get(p_id=any_id,u_id=request.user)
		elif type_of=='post_file':
			action_object=post_file_actions.objects.get(pf_id=any_id,u_id=request.user)
		action_object.datetime=local
		if int(action)==0:
			if action_object.ld_status==0:
				action_object.save(update_fields=['latest_datetime'])
			elif action_object.ld_status==1:
				action_object.ld_status=0
				post_file_obj.no_of_dislikes+=1
				if post_file_obj.no_of_likes >0:
					post_file_obj.no_of_likes-=1
				post_file_obj.save(update_fields=['no_of_dislikes','no_of_likes'])
			action_object.save(update_fields=['ld_status','latest_datetime'])
		elif int(action)==1:
			if action_object.ld_status==1:
				action_object.save(update_fields=['latest_datetime'])
			elif action_object.ld_status==0:
				action_object.ld_status=1
				post_file_obj.no_of_likes+=1
				if post_file_obj.no_of_dislikes >0:
					post_file_obj.no_of_dislikes-=1
				post_file_obj.save(update_fields=['no_of_dislikes','no_of_likes'])
			action_object.save(update_fields=['ld_status','latest_datetime'])
		elif int(action)==2:
			action_object.report_status=1
			post_file_obj.no_of_reports+=1
			action_object.save(update_fields=['report_status','latest_datetime'])
			post_file_obj.save(update_fields=['no_of_reports'])
		elif int(action)==3:
			action_object.report_status=0
			if post_file_obj.no_of_reports >0:
				post_file_obj.no_of_reports-=1
			action_object.save(update_fields=['report_status','latest_datetime'])
			post_file_obj.save(update_fields=['no_of_reports'])
	except:
		if type_of=='post_file':
			if int(action)==1 or int(action)==0:
				pfa_obj=post_file_actions(latest_datetime=local,pf_id=post_file_obj,u_id=request.user,ld_status=action)
			elif int(action)==2:
				pfa_obj=post_file_actions(latest_datetime=local,pf_id=post_file_obj,u_id=request.user,report_status=1)
			elif int(action)==3:
				pfa_obj=post_file_actions(latest_datetime=local,pf_id=post_file_obj,u_id=request.user,report_status=0)
		elif type_of=='post':
			if int(action)==1 or int(action)==0:
				pfa_obj=post_actions(latest_datetime=local,p_id=post_file_obj,u_id=request.user,ld_status=action)
			elif int(action)==2:
				pfa_obj=post_actions(latest_datetime=local,p_id=post_file_obj,u_id=request.user,report_status=1)
			elif int(action)==3:
				pfa_obj=post_actions(latest_datetime=local,p_id=post_file_obj,u_id=request.user,report_status=0)
		pfa_obj.save()
	return redirect(request, 'archile/index.html')


def add_thread(request,place,any_id):
	if request.method == "POST":
		utc = arrow.utcnow()
		local = utc.to('Asia/Kolkata')
		if place == 'posts':
			comment = request.POST['comment']
			typ = request.POST['typ']
			post_obj = Post.objects.get(p_id=any_id)
			post_thread_obj = Post_threads(u_id=request.user,p_id=post_obj,typ=typ,description=comment,creation_datetime=local)
			post_thread_obj.save()
			return redirect(post,any_id)
		if place == 'channel':
			return redirect(channel,any_id)
	return redirect(index)

def add_reply(request,place,any_id):
	if request.method == "POST":
		utc = arrow.utcnow()
		local = utc.to('Asia/Kolkata')
		if place == 'posts':
			comment = request.POST['comment']
			typ = request.POST['typ']
			pt_obj = Post_threads.objects.get(pt_id=any_id)
			post_obj = pt_obj.p_id
			post_thread_obj = Post_threads(u_id=request.user,p_id=post_obj,typ=typ,description=comment,creation_datetime=local,pt_id_reply_to=pt_obj)
			post_thread_obj.save()
			return redirect(post,post_obj.p_id)
		if place == 'channel':
			return redirect(channel,any_id)
	return redirect(index)