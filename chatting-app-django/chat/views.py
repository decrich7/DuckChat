from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from rest_framework.parsers import JSONParser
from chat.models import Message, Profile
from chat.forms import SignUpForm
from chat.serializers import MessageSerializer, UserSerializer
from . import RSA


def index(request):
    if request.user.is_authenticated:
        return redirect('chats')
    if request.method == 'GET':
        return render(request, 'chat/index.html', {})
    if request.method == "POST":
        username, password = request.POST['username'], request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
        else:
            return HttpResponse('{"error": "User does not exist"}')
        return redirect('chats')


def user(request):
    return render(request, 'chat/lk.html', {})


class SearchResultsView(ListView):
    model = User
    template_name = 'chat/search_results.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        object_list = User.objects.filter(
            Q(name__icontains=query) | Q(state__icontains=query)
        )
        return object_list


@csrf_exempt
def message_list(request, sender=None, receiver=None):
    if request.method == 'GET':

        rsa = RSA.Rsa()
        secret_key = Profile.objects.get(user=receiver)
        messages = Message.objects.filter(sender_id=sender, receiver_id=receiver, is_read=False)
        for messag in messages:
            print((messag.message))
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        for message in messages:
            message.is_read = True
            message.save()
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        user_id = User.objects.get(username=data['receiver'])
        print(user_id.id)
        open_key = Profile.objects.get(user=user_id.id)
        print(open_key.open_key)
        rsa1 = RSA.Rsa()
        data['message'] = rsa1.encript(data['message'], open_key.open_key)
        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


def register_view(request):
    if request.method == 'POST':
        print("working1")
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user.set_password(password)
            user.save()
            user = authenticate(username=username, password=password)
            # print(user.id, 13241234424244234)
            # Profile.objects.filter(id=user.id).update(secret_key='ddd', open_key='3123')
            rsa = RSA.Rsa()

            key = Profile()
            key.secret_key = rsa.get_secret_key()
            key.open_key = rsa.get_open_key()
            key.user = int(user.id)
            key.save()
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('chats')
    else:
        print("working2")
        form = SignUpForm()
    template = 'chat/register.html'
    context = {'form': form}
    return render(request, template, context)



def chat_view(request):
    if not request.user.is_authenticated:
        return redirect('index')
    if request.method == "GET":
        query = request.GET.get('q')
        return render(request, 'chat/chat.html',
                      {'users': User.objects.filter(pk=query)})


def message_view(request, sender, receiver):
    if not request.user.is_authenticated:
        return redirect('index')
    if request.method == "GET":
        return render(request, "chat/messages.html",
                      {'users': User.objects.exclude(username=request.user.username),
                       'receiver': User.objects.get(id=receiver),
                       'messages': Message.objects.filter(sender_id=sender, receiver_id=receiver) |
                                   Message.objects.filter(sender_id=receiver, receiver_id=sender)})
