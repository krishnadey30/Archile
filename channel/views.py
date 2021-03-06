from django.shortcuts import render, redirect
import datetime
from .models import *
import requests,arrow
from django.contrib.auth import authenticate, login as auth_login,logout
from django.contrib.auth.decorators import login_required
from django.db.models.fields.related import ManyToManyField
from django.views.decorators.cache import cache_control
import os
from django.conf import settings
from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import Paginator
from django.template import RequestContext
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.http import HttpResponse,HttpResponseRedirect
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .tokens import account_activation_token,password_reset_token
from django.core.mail import EmailMessage

from . forms import UserForm,PasswordForm

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

def Send_Email(to_address,subject, text):

	message = MIMEMultipart()
	message['From'] = "iiits.archile@gmail.com"
	message['To'] = to_address

	message["Subject"] = subject
	body = text
	message.attach(MIMEText(body, 'html'))
	password = "Archile!23"

	smtpObj = smtplib.SMTP_SSL('smtp.googlemail.com', 465)
	smtpObj.login(message['From'], password)
	smtpObj.sendmail(message['From'], message['To'], message.as_string())         
	smtpObj.quit()

#Send_Email("krishnakumar.d16@iiits.in", "Welcome to Archile!","<i>Archile</i> is an online platform where you can find and share valuable resources. Everything on <i>Archile</i> is very simple.<br><ul><li><b><i>Search</i></b> for resources by providing keywords.</li><li><b><i>Like</i></b> resources which you think are relevant and useful in particular channels. If not, <b><i>Dislike</i></b> them.</li><li><b><i>Report</i></b> resources you find disturbing and irrelevant.</li><li><b><i>Create Channels</i></b> and <b><i>Create Posts</i></b> to share your knowledge.</li><li>Add relevant <i><b>tags</b></i> while creating channels and posts to make the resources easier to search. </li></ul>Thank you for using <i>Archile</i>.")

#'http://34.222.42.228/archile/auth/user/'
#'http://'+current_site.domain+'/archile/auth/user/'
def change_call_back(request):
	current_site = get_current_site(request)
	payload = {'clientId':'5bd17f19d9aa55001529f8fb', 'secret':"6d5fc80be2b62f1eb699f1be6bfc44394de1e2e18f7fd825a7cf045e9825b5ac2d5661b924965f49b97d6827a5bbd298e1549660d43ea70c5830af0241ff3482",
'url':'http://'+current_site.domain+'/archile/auth/user/'
}
	url = "https://serene-wildwood-35121.herokuapp.com/oauth/changeUrl"
	#print(payload)
	response=requests.post(url, data=payload)
	data=response.json()
	#print(data)





# login - logout


#sending mail for password reset
def password_mail(user,request):

    current_site = get_current_site(request)
    message = render_to_string('archile/password_reset_email.html', {
        'user':user, 
        'domain':current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        'token': password_reset_token.make_token(user),
    })
    print("password reset")
    mail_subject = 'Reset Password of Archile Account.'
    to_email = user.email
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()

#sending mail for activation
def activation_mail(user,request):
    current_site = get_current_site(request)
    message = render_to_string('archile/acc_active_email.html', {
        'user':user, 
        'domain':current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        'token': account_activation_token.make_token(user),
    })
    mail_subject = 'Account Activation Mail -  Archile'
    to_email = user.email
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()

#new registration
def register(request):
    # Like before, get the request's context.
    if request.user.is_authenticated:
        return redirect('/')
    context = RequestContext(request)
    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        
        # If the two forms are valid...
        if user_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save(commit=False)

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.is_active = False
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            # user_profile = UserProfile(user=user)
            # user_profile.save()

            activation_mail(user,request)
            return HttpResponse('Please confirm your email address to complete the registration')
        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print(user_form.errors)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
    # Render the template depending on the context.
    return render(request,'archile/login1.html',{'user_form': user_form,'registered': registered})


#request a new confirmation mail.
def new_confirmation_mail(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
            if user:
                if user.is_active == False:
                    activation_mail(user,request)
                    return HttpResponse('Activation Link has been sent')
                else:
                    return HttpResponse('Account already activated')
        except:
            msg="No user with email : {} exist".format(email)
            return HttpResponse(msg)
    else:
        return render(request,'archile/confirmation.html', {})


#user login view
def user_login(request):
    # Like before, obtain the context for the user's request.
    if request.user.is_authenticated:
        return redirect('/')
    context = RequestContext(request)

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        email = request.POST['email']
        password = request.POST['password']
        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        try:
            user = User.objects.get(email=email)
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                user = authenticate(email=email, password=password)
                auth_login(request, user)
                return HttpResponseRedirect('/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your account is disabled.")
        except:
            # Bad login details were provided. So we can't log the user in.
            print ("Invalid login details: {0}".format(email))
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        user_form = UserForm()
        return render(request,'archile/login1.html', {'user_form': user_form})



#view for account activation
def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        auth_login(request, user)
        return render(request,'archile/information.html', {'message':'Thank you for your email confirmation. You will be redirected to Home page in sometime.'}) 
    else:
        return HttpResponse('Activation link is invalid!')



#user logout
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/')
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/')



#view for requestion password reset. It takes email as input and mailes the email with unique token

def request_reset(request):
    if request.method == 'POST':
        email = request.POST['email']
        print(email)
        try:
            user = User.objects.get(email=email)
            print(user.first_name)
            if user.email:
                #mailing unique token and link to the user
                password_mail(user,request)
                message = '''We've emailed you instructions for setting your password, if an account exists with the email you entered.
    You should receive them shortly.
    If you don't receive an email, please make sure you've entered the address you registered with,
    and check your spam folder.
    '''
                return render(request,'archile/information.html', {'message':message})
        except:
            msg="No user with email : {} exist".format(email)
            return HttpResponse(msg)
    else:
        return render(request,'archile/password_reset_form.html')


#verifying the reset password link and reseting the pasasword
def reset_password(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None
    if user is not None and password_reset_token.check_token(user, token):
        if request.method == 'POST':
            password_form = PasswordForm(data=request.POST)

            # If the two forms are valid...
            if password_form.is_valid():
                password=password_form.cleaned_data['password']
                user.set_password(password)
                user.save()
                message = 'Your password has been set. You will be redirected to SignIn page in sometime.'
                return render(request,'archile/information.html', {'message':message}) 
                
            else:
                print(password_form.errors)
        else:
            password_form = PasswordForm()
        return render(request,'archile/password_reset_confirm.html',{'form':password_form}) 
    else:
        return HttpResponse('Password link is invalid!')
        







@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def my_channels(request):
	user=request.user
	chan = Channel.objects.filter(u_id=user)
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

	return render(request,'archile/my_channels.html',{'channels':Channels_all})




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def index(request):
	Channels = Channel.objects.all()
	user = request.user
	Channels_all=[]
	for each in Channels:
		data = to_dict(each)
		try:
			subs = Subscription.objects.get(c_id=data['c_id'],u_id=user)
			data['subs'] = True
		except:
			data['subs'] = False
		
		Channels_all.append(data)
	page = request.GET.get('page', 1)
	paginator = Paginator(Channels_all, 3)
	try:
		mostsubs_Channels = paginator.page(page)
	except PageNotAnInteger:
		mostsubs_Channels = paginator.page(1)
	except EmptyPage:
		mostsubs_Channels = paginator.page(paginator.num_pages)
	# mostsubs_Channels=[]
	# for each in Channels:
	# 	if each.no_of_subscriptions>0:
	# 		mostsubs_Channels.append(each)
	# print(mostsubs_Channels)
	# mostsubs_Channels.sort(key=lambda d:d.no_of_subscriptions,reverse=True)
	context = {
	            'channels' : mostsubs_Channels
	}

	return render(request,'archile/index.html',context)


# def user_login(request):
# 	# change_call_back(request)
# 	return render(request,'archile/login.html')

#user logout
# @cache_control(no_cache=True, must_revalidate=True, no_store=True)
# @login_required(login_url='/user_login')
# def user_logout(request):
#     # Since we know the user is logged in, we can now just log them out.
#     logout(request)

#     # Take the user back to the homepage.
#     return redirect(user_login)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def search(request):

	user=request.user
	try:
		query =request.GET['search_query']
		text = query.lower().split()
		search_type = request.GET['search_type']
		page = request.GET.get('page', 1)
		Channels_all=[]
		Posts_all=[]
		if search_type == 'Channel':
			Channels = Channel.objects.all()
			Ch=[]
			for word in text:
				Ch.append(Channels.filter(name__icontains=word))
			#print(Ch)
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
			#print(Channels_all)
			paginator = Paginator(Channels_all, 4)
			try:
				Channels_all = paginator.page(page)
			except PageNotAnInteger:
				Channels_all = paginator.page(1)
			except EmptyPage:
				Channels_all = paginator.page(paginator.num_pages)
			
		else:
			Posts = Post.objects.all()
			Ps=[]
			for word in text:
				Ps.append(Posts.filter(title__icontains=word))
			ps_set = set()
			for pst in Ps:
				for each in pst:
					if each.p_id not in ps_set:
						data = to_dict(each)
						ps_set.add(data['p_id'])
						Posts_all.append(data)
			Posts_all=sorted(Posts_all,key=lambda d:[-d['no_of_likes'],d['no_of_dislikes'],d['creation_datetime']])
			paginator = Paginator(Posts_all, 4)
			try:
				Posts_all = paginator.page(page)
			except PageNotAnInteger:
				Posts_all = paginator.page(1)
			except EmptyPage:
				Posts_all = paginator.page(paginator.num_pages)
			
		context = {
			'channels': Channels_all,
			'posts': Posts_all,
			'query': query
		}
		return render(request, 'archile/search_results.html',context)
	except:
		return redirect(index)
	


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
	user_object.set_unusable_password()
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
		tags = list(set(map(lambda tag:tag.strip(),request.POST['channel_tags'].split(','))))
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
		tags = list(set(map(lambda tag:tag.strip().lower(),request.POST['post_tags'].split(','))))

		#getting all files
		FILES = ['AUDIO','VIDEO','IMAGES','DOCS','ARCHIVES']
		file_data={}
		for file in FILES:
			if file in request.FILES:
				file_data[file] = request.FILES.getlist(file)

		utc = arrow.utcnow()
		#print(utc)
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

		all_subscribers = Subscription.objects.filter(c_id=c_id)
		message = "New Post Added with title {} by {}.".format(title,user.email)
		for each_subscriber in all_subscribers:
			Send_Email(each_subscriber.u_id.email, "New Post Added in channel {}".format(ch.name),message)


		return redirect(channel,c_id)
	return redirect(index)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def edit_post(request,p_id):
	post_obj=Post.objects.get(p_id=p_id)
	post_tag_object = Post_tags.objects.filter(p_id=post_obj)
	context = {'post':post_obj,'tags':post_tag_object}
	post_old_tags = []
	for tags in post_tag_object:
		post_old_tags.append(tags.t_id.tag_name)
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
			#print(postf_obj.file)
			postf_obj.save()

		#eedit tags
		post_tags = list(map(lambda tag:tag.strip(),request.POST['post_tags'].split(',')))
		old_tags = list(set(post_old_tags).difference(set(post_tags)))
		for tag in old_tags:
			tag_obj = Tags.objects.get(tag_name=tag)
			old_tag_obj = Post_tags.objects.filter(t_id=tag_obj,p_id=post_obj)
			tag_obj.no_of_use-=1
			tag_obj.save()
			old_tag_obj.delete()
		new_tags = list(set(post_tags).difference(set(post_old_tags)))
		for tag in new_tags:
			try:
				tag_obj=Tags.objects.get(tag_name=tag)
				tag_obj.no_of_use+=1
			except:
				tag_obj = Tags(tag_name=tag,no_of_use = 1)
			tag_obj.save()
			post_tag=Post_tags(p_id=post_obj,t_id=tag_obj)
			post_tag.save()

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
	channel_obj=Channel.objects.get(c_id=c_id)
	channel_tag_object = Channel_tags.objects.filter(c_id=channel_obj)
	channel_old_tags = []
	for tags in channel_tag_object:
		channel_old_tags.append(tags.t_id.tag_name)
	context = {'channel':channel_obj,'tags':channel_old_tags}
	if request.method == 'POST':
		description = request.POST['channel_description']
		channel_obj.description=description
		try:
			logo = request.POST['old_logo']
			channel_obj.logo.delete(save=True)
		except:
			pass
		channel_tags = list(map(lambda tag:tag.strip(),request.POST['channel_tags'].split(',')))


		old_tags = list(set(channel_old_tags).difference(set(channel_tags)))
		for tag in old_tags:
			tag_obj = Tags.objects.get(tag_name=tag)
			old_tag_obj = Channel_tags.objects.filter(t_id=tag_obj,c_id=channel_obj)
			tag_obj.no_of_use-=1
			tag_obj.save()
			old_tag_obj.delete()
		new_tags = list(set(channel_tags).difference(set(channel_old_tags)))
		for tag in new_tags:
			try:
				tag_obj=Tags.objects.get(tag_name=tag)
				tag_obj.no_of_use+=1
			except:
				tag_obj = Tags(tag_name=tag,no_of_use = 1)
			tag_obj.save()
			channel_tag=Channel_tags(c_id=channel_obj,t_id=tag_obj)
			channel_tag.save()

		if 'channel_logo' in request.FILES:
			logo = request.FILES['channel_logo']
			channel_obj.logo = logo
		channel_obj.save()
		return redirect(channel,c_id)

	return render(request, 'archile/edit_channel.html', context)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')	
def subscribe_channel(request,c_id):
	Chan_obj = Channel.objects.get(c_id=c_id)
	count =Chan_obj.no_of_subscriptions
	user = request.user
	utc = arrow.utcnow()
	local = utc.to('Asia/Kolkata')
	try:
		subs_obj = Subscription.objects.get(c_id=Chan_obj,u_id=user)
		Chan_obj.no_of_subscriptions = count -1
		subs_obj.delete()
	except:
		subs_obj = Subscription(c_id=Chan_obj,u_id=user,s_datetime=local)
		if count == None:
			Chan_obj.no_of_subscriptions = 1
		else:
			Chan_obj.no_of_subscriptions = count + 1
		subs_obj.save()
	Chan_obj.save()
	# message = "You are Subscribeed to the channel {}".format(Chan_obj)

	# Send_Email(user.email, "Subscribed!",message)

	return redirect(my_subscriptions)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def post(request,p_id):
	post_obj = Post.objects.get(p_id=p_id)
	user = request.user
	try:
		cur_user_pst_act_obj = post_actions.objects.get(p_id=post_obj,u_id=user)
		if cur_user_pst_act_obj.ld_status == 1:
			post_obj.ld_status = True
		elif cur_user_pst_act_obj.ld_status == 0:
			post_obj.ld_status = False
		else:
			post_obj.ld_status = None
		if cur_user_pst_act_obj.report_status == 1:
			post_obj.report_status = True
		elif cur_user_pst_act_obj.report_status == 0:
			post_obj.report_status = False
		else:
			post_obj.report_status = None
	except:
		post_obj.ld_status = None
		post_obj.report_status = None
	context={}
	context['post'] = post_obj
	files = Post_files.objects.filter(p_id=p_id)
	thread_obj = Post_threads.objects.filter(p_id=p_id,pt_id_reply_to=None)
	post_files = []
	post_threads = []
	for f in files:
		p=str(f.file)
		f.filename=p.split('/')[1]
		f.upload_datetime =arrow.get(f.upload_datetime).format('Do MMMM YYYY')
		try:
			cur_user_pf_act_obj = post_file_actions.objects.get(pf_id=f,u_id=user)
			if cur_user_pf_act_obj.ld_status == 1:
				f.ld_status = True
			elif cur_user_pf_act_obj.ld_status == 0:
				f.ld_status = False
			else:
				f.ld_status = None
			if cur_user_pf_act_obj.report_status == 1:
				f.report_status = True
			elif cur_user_pf_act_obj.report_status == 0:
				f.report_status = False
			else:
				f.report_status = None
		except:
			f.report_status = None
			f.ld_status = None
		post_files.append(f)
	for thread in thread_obj:
		reply_thread = Post_threads.objects.filter(pt_id_reply_to=thread)
		try:
			cur_user_pt_act_obj = post_thread_actions.objects.get(pt_id=thread,u_id=user)
			thread.ld_status=cur_user_pt_act_obj.ld_status
			thread.report_status=cur_user_pt_act_obj.report_status
		except:
			thread.report_status = None
			thread.ld_status = None
		reply_threads=[]
		for each in reply_thread:
			try:
				cur_user_pt_act_obj = post_thread_actions.objects.get(pt_id=each,u_id=user)
				each.ld_status=cur_user_pt_act_obj.ld_status
				each.report_status=cur_user_pt_act_obj.report_status
			except:
				each.report_status = None
				each.ld_status = None
			reply_threads.append(each)

		val = [thread,reply_threads]
		post_threads.append(val)
	context['post_files'] = post_files
	context['post_threads'] = post_threads
	return render(request, 'archile/post.html',context)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def report_channel(request, c_id):
	user = request.user
	channel_object = Channel.objects.get(c_id=c_id)
	try:
		channel_act_obj = channel_actions.objects.get(c_id = channel_object,u_id=user)
		#print(channel_act_obj.report_status)
		if channel_act_obj.report_status == True:
			channel_act_obj.report_status = False
			channel_object.no_of_reports-=1
		elif channel_act_obj.report_status == False:
			channel_act_obj.report_status = True
			channel_object.no_of_reports+=1
	except:
		channel_act_obj = channel_actions()
		channel_act_obj.report_status = True
		channel_act_obj.u_id=user
		channel_act_obj.c_id = channel_object
		channel_object.no_of_reports+=1
	channel_act_obj.save()
	if channel_object.no_of_reports >=1:
		channel_object.status = False
		channel_object.save()
	channel_object.save()
	return redirect(channel,c_id)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def channel(request,c_id):
	channel = Channel.objects.get(c_id=c_id)
	posts=Post.objects.filter(c_id=channel)
	user = request.user
	context = {}
	try:
		channel_actions_obj = channel_actions.objects.get(c_id = channel,u_id=user)
		channel.report_status = channel_actions_obj.report_status
	except:
		channel.report_status = None
	thread_obj = Channel_threads.objects.filter(c_id=channel,ct_id_reply_to=None)
	context['channel'] = channel
	context['posts']=[]
	context['docs']=[]
	context['images']=[]
	context['audio']=[]
	context['video']=[]
	context['archives']=[]
	for post in posts:
		post.creation_datetime=arrow.get(post.creation_datetime).format('Do MMMM YYYY')
		try:
			cur_user_pst_act_obj = post_actions.objects.get(p_id=post,u_id=user)
			if cur_user_pst_act_obj.ld_status == 1:
				post.ld_status = True
			elif cur_user_pst_act_obj.ld_status == 0:
				post.ld_status = False
			else:
				post.ld_status = None
			if cur_user_pst_act_obj.report_status == 1:
				post.report_status = True
			elif cur_user_pst_act_obj.report_status == 0:
				post.report_status = False
			else:
				post.report_status = None
		except:
			post.ld_status = None
			post.report_status = None
		context['posts'].append(post)
		files=Post_files.objects.filter(p_id=post.p_id)
		for f in files:
			p=str(f.file)
			f.filename=p.split('/')[1]
			f.upload_datetime =arrow.get(f.upload_datetime).format('Do MMMM YYYY')
			try:
				cur_user_pf_act_obj = post_file_actions.objects.get(pf_id=f,u_id=user)
				if cur_user_pf_act_obj.ld_status == 1:
					f.ld_status = True
				elif cur_user_pf_act_obj.ld_status == 0:
					f.ld_status = False
				else:
					f.ld_status = None
				if cur_user_pf_act_obj.report_status == 1:
					f.report_status = True
				elif cur_user_pf_act_obj.report_status == 0:
					f.report_status = False
				else:
					f.report_status = None
			except:
				f.report_status = None
				f.ld_status = None

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

	channel_threads=[]
	for thread in thread_obj:
		reply_thread = Channel_threads.objects.filter(ct_id_reply_to=thread)
		try:
			cur_user_pt_act_obj = channel_thread_actions.objects.get(ct_id=thread,u_id=user)
			thread.ld_status=cur_user_pt_act_obj.ld_status
			thread.report_status=cur_user_pt_act_obj.report_status
		except:
			thread.report_status = None
			thread.ld_status = None
		reply_threads=[]
		for each in reply_thread:
			try:
				cur_user_pt_act_obj = channel_thread_actions.objects.get(ct_id=each,u_id=user)
				each.ld_status=cur_user_pt_act_obj.ld_status
				each.report_status=cur_user_pt_act_obj.report_status
			except:
				each.report_status = None
				each.ld_status = None
			reply_threads.append(each)

		val = [thread,reply_threads]
		channel_threads.append(val)

	context['channel_threads'] = channel_threads
	try:
		subs = Subscription.objects.get(c_id=channel,u_id=user)
		context['subs'] = True
	except:
		context['subs'] = False
	return render(request, 'archile/channel.html',context)




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')	
def download(request, path,pf_id):
	pf_obj = Post_files.objects.get(pf_id=pf_id)
	user = request.user
	utc = arrow.utcnow()
	local = utc.to('Asia/Kolkata')
	download_obj = Dowload_history(pf_id=pf_obj,u_id=user,download_datetime=local)
	download_obj.save()
	path='post_files/'+path
	file_path = os.path.join(settings.MEDIA_ROOT, path)
	if os.path.exists(file_path):
		with open(file_path, 'rb') as fh:
			response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
			response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
			return response
	raise Http404



# if action=0 -->dislike, action=1-->like ,action=2 -->report,action=3-->unreport
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def actions(request,type_of,action,any_id):
	utc = arrow.utcnow()
	local = utc.to('Asia/Kolkata')
	next_url = request.GET['next']
	# retrieving the respective post or post_file on which action is performed
	if type_of=='posts':
		post_file_obj=Post.objects.get(p_id=any_id)
	elif type_of=='post_file':
		post_file_obj=Post_files.objects.get(pf_id=any_id)
	# enters "try" only if the any action object(like,dislike,report,unreport) is already in the database and it is to be modified
	try:
		#respective post or post_file action object gets retrieved
		if type_of=='posts':
			action_object=post_actions.objects.get(p_id=any_id,u_id=request.user)
		elif type_of=='post_file':
			action_object=post_file_actions.objects.get(pf_id=any_id,u_id=request.user)
		action_object.datetime=local
		#if action==dislike 
		if int(action)==0:
			if action_object.ld_status==0:         #if already disliked dont make any changes except datetime
				action_object.ld_status = None
				post_file_obj.no_of_dislikes-=1
				post_file_obj.save()
				action_object.save(update_fields=['latest_datetime'])
			elif action_object.ld_status==None:    #if ld_status is None make it disliked i.e(ld_status=0) and increase the no_of_dislikes
				action_object.ld_status=0
				post_file_obj.no_of_dislikes+=1
				post_file_obj.save()
				#if ld_status=1 (i.e it is already liked and user wants to dislike it then make ld_status=0 (i.e disliking it) 
				#and increase the number of dislikes and increase the number of likes by 1
			elif action_object.ld_status==1:      
				action_object.ld_status=0
				post_file_obj.no_of_dislikes+=1
				if post_file_obj.no_of_likes >0:
					post_file_obj.no_of_likes-=1
				post_file_obj.save(update_fields=['no_of_dislikes','no_of_likes'])
			action_object.save(update_fields=['ld_status','latest_datetime'])
		#if action==like
		elif int(action)==1:
			if action_object.ld_status==1:
				action_object.ld_status = None
				post_file_obj.no_of_likes-=1
				post_file_obj.save()
				action_object.save(update_fields=['latest_datetime'])
			elif action_object.ld_status==None:
				action_object.ld_status=1
				post_file_obj.no_of_likes+=1
				post_file_obj.save()
			elif action_object.ld_status==0:
				action_object.ld_status=1
				post_file_obj.no_of_likes+=1
				if post_file_obj.no_of_dislikes >0:  #no_of_dislikes or likes or reports cant be negative
					post_file_obj.no_of_dislikes-=1
				post_file_obj.save(update_fields=['no_of_dislikes','no_of_likes'])
			action_object.save(update_fields=['ld_status','latest_datetime'])
		#if action==report
		elif int(action)==2:
			action_object.report_status=1
			post_file_obj.no_of_reports+=1
			action_object.save(update_fields=['report_status','latest_datetime'])
			post_file_obj.save(update_fields=['no_of_reports'])
		#if action==unreport
		elif int(action)==3:
			action_object.report_status=0
			if post_file_obj.no_of_reports >0:  
				post_file_obj.no_of_reports-=1
			action_object.save(update_fields=['report_status','latest_datetime'])
			post_file_obj.save(update_fields=['no_of_reports'])
	#enters except if action object enters the database newly
	except:
		if type_of=='post_file':
			#creating the action object for post_files
			if int(action)==1 or int(action)==0:
				pfa_obj=post_file_actions(latest_datetime=local,pf_id=post_file_obj,u_id=request.user,ld_status=int(action))

			elif int(action)==2:
				pfa_obj=post_file_actions(latest_datetime=local,pf_id=post_file_obj,u_id=request.user,report_status=1)
				
			elif int(action)==3:
				pfa_obj=post_file_actions(latest_datetime=local,pf_id=post_file_obj,u_id=request.user,report_status=0)
		elif type_of=='posts':
			#creating the action object for posts
			if int(action)==1 or int(action)==0:
				pfa_obj=post_actions(latest_datetime=local,p_id=post_file_obj,u_id=request.user,ld_status=int(action))
			elif int(action)==2:
				pfa_obj=post_actions(latest_datetime=local,p_id=post_file_obj,u_id=request.user,report_status=1)
			elif int(action)==3:
				pfa_obj=post_actions(latest_datetime=local,p_id=post_file_obj,u_id=request.user,report_status=0)
		pfa_obj.save()
		#increasing the number of likes or dislikes or reports accordingly
		if int(action)==0:
			post_file_obj.no_of_dislikes+=1
			post_file_obj.save(update_fields=['no_of_dislikes'])
		elif int(action)==1:
			post_file_obj.no_of_likes+=1
			post_file_obj.save(update_fields=['no_of_likes'])
		elif int(action)==2:
			post_file_obj.no_of_reports+=1
			post_file_obj.save(update_fields=['no_of_reports'])
		elif int(action)==3:
			post_file_obj.no_of_reports-=1
			post_file_obj.save(update_fields=['no_of_reports'])

	if type_of =='posts':
		if next_url == 'post':
			return redirect(post,any_id)
		elif next_url == 'channel':
			return redirect(channel,post_file_obj.c_id.c_id)
	else:
		if next_url == 'post':
			return redirect(post,post_file_obj.p_id.p_id)
		elif next_url == 'channel':
			return redirect(channel,post_file_obj.p_id.c_id.c_id)
	return HttpResponse("Redirecting onto other pages not working:(")



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def add_thread(request,place,any_id):
	if request.method == "POST":
		utc = arrow.utcnow()
		local = utc.to('Asia/Kolkata')
		comment = request.POST['comment']
		typ = request.POST['typ']
		if place == 'posts':
			post_obj = Post.objects.get(p_id=any_id)
			post_thread_obj = Post_threads(u_id=request.user,p_id=post_obj,typ=typ,description=comment,creation_datetime=local)
			post_thread_obj.save()
			return redirect(post,any_id)
		if place == 'channel':
			channel_obj = Channel.objects.get(c_id=any_id)
			channel_thread_obj =Channel_threads(u_id=request.user,c_id=channel_obj,typ=typ,description=comment,creation_datetime=local)
			channel_thread_obj.save()
			return redirect(channel,any_id)

	return redirect(index)




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def add_reply(request,place,any_id):
	if request.method == "POST":
		utc = arrow.utcnow()
		local = utc.to('Asia/Kolkata')
		comment = request.POST['comment']
		typ = request.POST['typ']
		if place == 'posts':
			pt_obj = Post_threads.objects.get(pt_id=any_id)
			post_obj = pt_obj.p_id
			post_thread_obj = Post_threads(u_id=request.user,p_id=post_obj,typ=typ,description=comment,creation_datetime=local,pt_id_reply_to=pt_obj)
			post_thread_obj.save()
			return redirect(post,post_obj.p_id)
		if place == 'channel':
			ct_obj = Channel_threads.objects.get(ct_id=any_id)
			channel_obj = ct_obj.c_id
			channel_thread_obj = Channel_threads(u_id=request.user,c_id=channel_obj,typ=typ,description=comment,creation_datetime=local,ct_id_reply_to=ct_obj)
			channel_thread_obj.save()
			# send_mail = Channel_threads.objects.filter(ct_id_reply_to=ct_obj) 
			# send_mail = set([user.u_id.email for user in send_mail])
			# send_mail.add(ct_obj.u_id.email)
			# message = " There is a new reply in the channel {} where you have commented earlier.".format(channel_obj.name)
			# for each in send_mail:
			# 	Send_Email(each, "Got a Reply",message)
			all_subscribers = Subscription.objects.filter(c_id=channel_obj)
			message = " There is a new reply in the channel {} where you have commented earlier.".format(channel_obj.name)
			for each_subscriber in all_subscribers:
				Send_Email(each_subscriber.u_id.email, "New Reply in",message)

			return redirect(channel,channel_obj.c_id)
	return redirect(index)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def post_thread_action(request,pt_id,typ):
	pt_obj = Post_threads.objects.get(pt_id=pt_id)
	#print(pt_obj.pt_id)
	user = request.user
	typ = int(typ)
	utc = arrow.utcnow()
	local = utc.to('Asia/Kolkata')
	try:
		pt_act_obj = post_thread_actions.objects.get(u_id=user,pt_id=pt_obj)
		#print(pt_act_obj.ld_status)
		if typ == 1:
			if pt_act_obj.ld_status == 1:
				pt_act_obj.ld_status = None
				pt_obj.no_of_likes -=1
			elif pt_act_obj.ld_status == 0:
				pt_act_obj.ld_status = 1
				pt_obj.no_of_likes+=1
				pt_obj.no_of_dislikes-=1
			elif pt_act_obj.ld_status == None:
				pt_act_obj.ld_status = 1
				pt_obj.no_of_likes+=1
		elif typ == 0:
			if pt_act_obj.ld_status == 0:
				pt_act_obj.ld_status = None
				pt_obj.no_of_dislikes -=1
			elif pt_act_obj.ld_status == 1:
				pt_act_obj.ld_status = 0
				pt_obj.no_of_dislikes+=1
				pt_obj.no_of_likes-=1
			elif pt_act_obj.ld_status == None:
				pt_act_obj.ld_status = 0
				pt_obj.no_of_dislikes+=1
		elif typ == 2:
			if pt_act_obj.report_status == None or pt_act_obj.report_status == 0:
				pt_act_obj.report_status = 1
				pt_obj.no_of_reports+=1
			elif pt_act_obj.report_status == 1:
				pt_act_obj.report_status = 0
				pt_obj.no_of_reports-=1
	except:
		pt_act_obj = post_thread_actions()
		pt_act_obj.u_id=user
		pt_act_obj.pt_id=pt_obj
		if typ==1:
			pt_act_obj.ld_status = 1
			pt_obj.no_of_likes+=1
		elif typ == 0:
			pt_act_obj.ld_status = 0
			pt_obj.no_of_dislikes+=1
		elif typ == 2:
			pt_act_obj.report_status = 1
			pt_obj.no_of_reports+=1
	pt_obj.save()
	pt_act_obj.latest_datetime = local
	pt_act_obj.save()
	return redirect(post,pt_obj.p_id.p_id)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def channel_thread_action(request,ct_id,typ):
	ct_obj = Channel_threads.objects.get(ct_id=ct_id)
	user = request.user
	typ = int(typ)
	utc = arrow.utcnow()
	local = utc.to('Asia/Kolkata')
	try:
		ct_act_obj = channel_thread_actions.objects.get(u_id=user,ct_id=ct_obj)
		if typ == 1:
			if ct_act_obj.ld_status == 1:
				ct_act_obj.ld_status = None
				ct_obj.no_of_likes -=1
			elif ct_act_obj.ld_status == 0:
				ct_act_obj.ld_status = 1
				ct_obj.no_of_likes+=1
				ct_obj.no_of_dislikes-=1
			elif ct_act_obj.ld_status == None:
				ct_act_obj.ld_status = 1
				ct_obj.no_of_likes+=1
		elif typ == 0:
			if ct_act_obj.ld_status == 0:
				ct_act_obj.ld_status = None
				ct_obj.no_of_dislikes -=1
			elif ct_act_obj.ld_status == 1:
				ct_act_obj.ld_status = 0
				ct_obj.no_of_dislikes+=1
				ct_obj.no_of_likes-=1
			elif ct_act_obj.ld_status == None:
				ct_act_obj.ld_status = 0
				ct_obj.no_of_dislikes+=1
		elif typ == 2:
			if ct_act_obj.report_status == None or ct_act_obj.report_status == 0:
				ct_act_obj.report_status = 1
				ct_obj.no_of_reports+=1
			elif ct_act_obj.report_status == 1:
				ct_act_obj.report_status = 0
				ct_obj.no_of_reports-=1
	except:
		ct_act_obj = channel_thread_actions()
		ct_act_obj.u_id=user
		ct_act_obj.ct_id=ct_obj
		if typ==1:
			ct_act_obj.ld_status = 1
			ct_obj.no_of_likes+=1
		elif typ == 0:
			ct_act_obj.ld_status = 0
			ct_obj.no_of_dislikes+=1
		elif typ == 2:
			ct_act_obj.report_status = 1
			ct_obj.no_of_reports+=1
	ct_obj.save()
	ct_act_obj.latest_datetime = local
	ct_act_obj.save()
	return redirect(channel,ct_obj.c_id.c_id)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def liked_posts(request):
	user = request.user
	liked_obj = post_actions.objects.filter(u_id=user,ld_status=1)
	context = {}
	context['posts']=[]
	for pst in liked_obj:
		post = pst.p_id
		post.creation_datetime=arrow.get(post.creation_datetime).format('Do MMMM YYYY')
		try:
			cur_user_pst_act_obj = post_actions.objects.get(p_id=post,u_id=user)
			if cur_user_pst_act_obj.ld_status == 1:
				post.ld_status = True
			elif cur_user_pst_act_obj.ld_status == 0:
				post.ld_status = False
			else:
				post.ld_status = None
			if cur_user_pst_act_obj.report_status == 1:
				post.report_status = True
			elif cur_user_pst_act_obj.report_status == 0:
				post.report_status = False
			else:
				post.report_status = None
		except:
			post.ld_status = None
			post.report_status = None
		context['posts'].append(post)
	
	return render(request,'archile/liked_posts.html',context)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='/user_login')
def my_subscriptions(request):
	user=request.user
	subs_obj = Subscription.objects.filter(u_id=user)
	Channels_all=[]
	for ech in subs_obj:
		each = ech.c_id
		data = to_dict(each)
		data['subs']=True
		Channels_all.append(data)
	Channels_all=sorted(Channels_all,key=lambda d:-d['no_of_subscriptions'])

	return render(request,'archile/my_subscriptions.html',{'channels':Channels_all})