
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Room, Topic, Message 
from .forms import RoomForm

rooms = Room.objects.all()

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, f'User "{username}" does not exist in the database')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Incorrect username or password')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error('An error occurred during registration.')

    return render(request, 'base/login_register.html', {'form': form})

def home(request, pk = ""):
    topics = Topic.objects.all()
    participants_count = ""
    
    try:
        q = request.GET.get('q') if request.GET.get('q') != None else ""
        rooms = Room.objects.filter(
            Q(topic__name__icontains=q) |
            Q(name__icontains=q) |
            Q(description__icontains=q)
        ) 
        if rooms.count() == 0:
            rooms_count = 'No'
        else:
            rooms_count = rooms.count()
        for room in rooms:
            participants_count = room.participants.all().count()
    except:
        rooms = "Your query did not return any results"
        participants_count = ""      

    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q)).order_by('-created')

    context = {'rooms': rooms, 'topics': topics, 'rooms_count': rooms_count, 'room_messages': room_messages, 'participants_count': participants_count }
    return render(request, "base/home.html", context)

def room(request, pk):
    room = Room.objects.get(id = pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages, 'participants': participants }
    return render(request, "base/room.html", context)

@login_required(login_url='login')
def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    rooms_count = rooms.count()

    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics, 'rooms_count': rooms_count }
    return render(request, 'base/profile.html', context)

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()
            return redirect('home')
    context = {'form': form}
    return render(request, 'base/create-room.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)

    if request.user != room.host: 
        message = 'You can only edit your rooms!!'
        context = {'message': message}
        return render(request, 'base/error.html', context)

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')
    context = {"form": form}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    
    if request.user != room.host: 
        message = 'You can only delete your rooms!!'
        context = {'message': message}
        return render(request, 'base/error.html', context)
    
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    context = {"form": form}
    return render(request, 'base/delete_form.html', {'obj': form})

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    
    if request.user != message.user: 
        message = 'You can only delete your messages!!'
        context = {'message': message}
        return render(request, 'base/error.html', context)
    
    if request.method == 'POST':
        message.delete()
        return redirect('room', pk=room.id)
    
    return render(request, 'base/delete_form.html', {'obj': message})