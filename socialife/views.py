from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from .models import MyUser, Post, Comment, Notification, ChatRoom, Message, PostImage, UserAvatar, UserProfile, HashTag
from .serializers import UserSerializer, PostSerializer, CommentSerializer, NotificationSerializer, ChatRoomSerializer, MessageSerializer, HashTagSerializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json
from .middlewares import check_user_with_token, convert_vn_to_eng, draw_graph, draw_network

from django.db.models import Q
import uuid
from django.core.files.storage import FileSystemStorage

import os

from django.conf import settings
from .search_engine import Search

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from django.db.models import Count

import networkx as nx
import numpy
import random
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.image as mpimg
from essential_generators import DocumentGenerator
import operator

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_logged_in(request):
    user_is_valid = check_user_with_token(request)
    data = json.loads(request.body.decode('utf-8'))
    if user_is_valid:
        notifications =  Notification.objects.filter(user = request.user).order_by('-pk')
        chat_rooms = request.user.chat_rooms.all().order_by('-last_interaction')
        try:
            if data['chat_room'] == True:
                for room in chat_rooms:
                    room.notice_by_users.add(request.user)
                    room.save()
                chat_rooms = request.user.chat_rooms.all().order_by('-last_interaction')
        finally:
            messages = Message.objects.filter(chat_room__in=chat_rooms).order_by('-date_created')
            followings = request.user.followings.all()
            return Response({'message': 'Authorized', 'user': UserSerializer(request.user).data,
            'notifications': NotificationSerializer(notifications, many=True).data,
            'messages': MessageSerializer(messages, many=True).data,
            'chat_rooms': ChatRoomSerializer(chat_rooms, many=True).data,
            'followings': UserSerializer(followings, many=True).data}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enter_chat_room(request):
    user_is_valid = check_user_with_token(request)
    data = json.loads(request.body.decode('utf-8'))
    if user_is_valid:
        target_profile_name = data['profile_name']
        target_user = MyUser.objects.filter(profile_name = target_profile_name)
        if len(target_user) == 1:
            # room = ChatRoom.objects.filter(Q(users__icontains = request.user) & Q(users__icontains = target_user[0]) & Q(is_group_chat = False))
            rooms = request.user.chat_rooms.all()
            existed_chat_room = None
            for room in rooms:
                if target_user[0] in room.users.all() and room.is_group_chat == False:
                    existed_chat_room = room
                    break
            if existed_chat_room != None:
                return Response({'message': 'Success', 'room': ChatRoomSerializer(existed_chat_room).data}, status=status.HTTP_200_OK)
            else:
                new_room = ChatRoom.objects.create()
                new_room.users.add(request.user)
                new_room.users.add(target_user[0])
                new_room.save()
                return Response({'message': 'Created', 'room': ChatRoomSerializer(new_room).data}, status=status.HTTP_201_CREATED)
    else:
        return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_new_post(request):
    user_is_valid = check_user_with_token(request)
    data = json.loads(request.body.decode('utf-8'))
    if user_is_valid:
        text_content = data['text_content']
        new_post = Post.objects.create(text_content = text_content, user = request.user)
        hashtags = data['hashtags']
        if len(hashtags) > 0:
            for hashtag in hashtags:
                existed_hashtag = HashTag.objects.filter(name = hashtag)
                if len(existed_hashtag) > 0:
                    new_post.hashtags.add(existed_hashtag[0])
                    existed_hashtag[0].most_recent = timezone.now()
                    existed_hashtag[0].save()
                else:
                    new_hashtag = HashTag.objects.create(name = hashtag)
                    new_post.hashtags.add(new_hashtag)
                new_post.save()

        return Response({'message': 'Success', 'post': PostSerializer(new_post).data}, status=status.HTTP_201_CREATED)
    else:
        return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_home_feed(request):
    user_is_valid = check_user_with_token(request)
    if user_is_valid:
        user_posts = Post.objects.filter(Q(user = request.user) | Q(user__in=request.user.followings.all())).order_by('-date_created')
        serializer = PostSerializer(user_posts, many = True).data
        one_month_ago = timezone.now() - timezone.timedelta(days = 30)
        trending_hashtags = HashTag.objects.filter(most_recent__gt = one_month_ago).annotate(count=Count('posts')).order_by('-count')[:5]
        return Response({'message': 'Authorized', 'user_posts': serializer, 'trending_hashtags': HashTagSerializer(trending_hashtags, many = True).data}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def check_profile_name_availability(request):
    data = json.loads(request.body.decode('utf-8'))
    request_profile_name = data['profile_name']
    user = MyUser.objects.filter(profile_name = request_profile_name)
    if len(user) == 0:
        return Response({'message': 'Available'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Taken'}, status=status.HTTP_406_NOT_ACCEPTABLE)

@api_view(['POST'])
def user_sign_up(request):
    email = request.POST['email']
    password = request.POST['password']
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    gender = request.POST['gender']
    profile_name = request.POST['profile_name']
    date_of_birth = request.POST['year'] + '-' + request.POST['month'] + '-' + request.POST['date']
    
    user = MyUser.objects.create(email=email,first_name=first_name,
    last_name=last_name,gender=gender.capitalize(),profile_name=profile_name, date_of_birth=date_of_birth)
    user.set_password(password)
    user.save()
    UserAvatar.objects.create(user = user, image = request.FILES['file'])

    return Response({'message': 'Available'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def get_user_profile(request):
    data = json.loads(request.body.decode('utf-8'))
    request_profile_name = data['profile_name']
    user = MyUser.objects.filter(profile_name = request_profile_name)
    if len(user) == 1:
        user_serializer = UserSerializer(user[0]).data
        followings = user[0].followings.all()
        followers = user[0].followers.all()
        user_posts = Post.objects.filter(user = user[0]).order_by('-date_created')
        post_serializer = PostSerializer(user_posts, many = True).data
        return Response({'message': 'Success', 'user': user_serializer, 'user_posts': post_serializer,
        'followings': UserSerializer(followings, many = True).data,
        'followers': UserSerializer(followers, many = True).data}, status=status.HTTP_200_OK)
    return Response({'message': 'Failed'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request):
    user_is_valid = check_user_with_token(request)
    data = json.loads(request.body.decode('utf-8'))
    if user_is_valid:
        target_profile_name = data['profile_name']
        target_user = MyUser.objects.filter(profile_name = target_profile_name)
        if len(target_user) == 1:
            if (target_user[0] != request.user):
                if target_user[0] in request.user.followings.all():
                    request.user.followings.remove(target_user[0])
                else:
                    request.user.followings.add(target_user[0])
                    notification = Notification.objects.create(user = target_user[0], from_user = request.user,
                    content='followed you', url='/profile/' + request.user.profile_name)
                    channel_layer = get_channel_layer()
                    if target_user[0].channel_name != '':
                        async_to_sync(channel_layer.send)(target_user[0].channel_name, {
                            "type": "new_notification",
                            'notification': NotificationSerializer(notification).data
                        })
                request.user.save()
                return Response({'message': 'Success'}, status=status.HTTP_200_OK)
            return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_a_post(request):
    user_is_valid = check_user_with_token(request)
    data = json.loads(request.body.decode('utf-8'))
    if user_is_valid:
        print(data)
        target_post_uuid = data['post_uuid']
        target_post = Post.objects.filter(uuid = target_post_uuid)
        if len(target_post) == 1:
            if not request.user in target_post[0].liked_by.all():
                target_post[0].liked_by.add(request.user)
                target_post[0].save()
                if request.user != target_post[0].user:
                    notification = Notification.objects.create(user = target_post[0].user, from_user = request.user,
                    content='liked one of your posts.')
                    channel_layer = get_channel_layer()
                    if target_post[0].user.channel_name != '':
                        async_to_sync(channel_layer.send)(target_post[0].user.channel_name, {
                            "type": "new_notification",
                            'notification': NotificationSerializer(notification).data
                        })
                return Response({'message': 'Liked'}, status=status.HTTP_200_OK)
            else:
                target_post[0].liked_by.remove(request.user)
                target_post[0].save()
                return Response({'message': 'Unliked'}, status=status.HTTP_200_OK)
        return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_a_post(request):
    user_is_valid = check_user_with_token(request)
    data = json.loads(request.body.decode('utf-8'))
    if user_is_valid:
        target_post_uuid = data['post_uuid']
        target_post = Post.objects.filter(uuid = target_post_uuid)
        if len(target_post) == 1:
            if target_post[0].user == request.user:
                target_post[0].delete()
                return Response({'message': 'Success'}, status=status.HTTP_200_OK)
            return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_a_comment(request):
    user_is_valid = check_user_with_token(request)
    data = json.loads(request.body.decode('utf-8'))
    if user_is_valid:
        print(data)
        target_post_uuid = data['post_uuid']
        target_post = Post.objects.filter(uuid = target_post_uuid)
        if len(target_post) == 1:
            comment = Comment.objects.create(user = request.user, content = data['content'], post = target_post[0])
            if request.user != target_post[0].user:
                notification = Notification.objects.create(user = target_post[0].user, from_user = request.user,
                content='commented on one of your posts.')
                channel_layer = get_channel_layer()
                if target_post[0].user.channel_name != '':
                    async_to_sync(channel_layer.send)(target_post[0].user.channel_name, {
                        "type": "new_notification",
                        'notification': NotificationSerializer(notification).data
                    })
            return Response({'message': 'Success', 'comment': CommentSerializer(comment).data}, status=status.HTTP_200_OK)
        return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def read_notifications(request):
    user_is_valid = check_user_with_token(request)
    data = json.loads(request.body.decode('utf-8'))
    if user_is_valid:
        Notification.objects.filter(user = request.user).update(is_read = True)
        return Response({'message': 'Success'}, status=status.HTTP_200_OK)
    return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_or_remove_bookmark(request):
    user_is_valid = check_user_with_token(request)
    data = json.loads(request.body.decode('utf-8'))
    if user_is_valid:
        target_post_uuid = data['post_uuid']
        target_post = Post.objects.filter(uuid = target_post_uuid)
        if len(target_post) == 1:
            if data['type'] == 'add':
                target_post[0].bookmarked_by.add(request.user)
            elif data['type'] == 'remove':
                target_post[0].bookmarked_by.remove(request.user)
            target_post[0].save()
            return Response({'message': 'Success'}, status=status.HTTP_200_OK)
        return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_picture(request):
    user_email = request.user.email
    request_email = request.POST['email']
    if user_email == request_email:
        post = Post.objects.filter(uuid = request.POST['uuid'])
        for image in request.FILES.getlist('file'):
            PostImage.objects.create(image = image, post = post[0])
        return Response({'message': 'Success'}, status=status.HTTP_200_OK)
    return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_avatar(request):
    user_email = request.user.email
    request_email = request.POST['email']
    if user_email == request_email:
        UserAvatar.objects.create(user = request.user, image = request.FILES['file'])
        return Response({'message': 'Success'}, status=status.HTTP_200_OK)
    return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def search(request):
    data = json.loads(request.body.decode('utf-8'))
    query = data['query']
    search_type = data['search_type']
    completion = data['completion']
    search = Search()
    if search_type == 'profile_name':
        search = search.search_by_profile_name(query, completion)
    elif search_type == 'name':
        search = search.search_by_name(query)
    if search.result != None:
        return Response({'message': 'Success', 'result': UserSerializer(search.result, many=True).data}, status=status.HTTP_200_OK)
    return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_trending_hashtags(request):
    one_month_ago = timezone.now() - timezone.timedelta(days = 30)
    trending_hashtags = HashTag.objects.filter(most_recent__gt = one_month_ago).annotate(count=Count('posts')).order_by('-count')[:5]
    return Response({'message': 'Success', 'trending_hashtags': HashTagSerializer(trending_hashtags, many = True).data}, status=status.HTTP_200_OK)

@api_view(['POST'])
def get_bookmark(request):
    user_is_valid = check_user_with_token(request)
    data = json.loads(request.body.decode('utf-8'))
    if user_is_valid:
        posts = request.user.bookmarked_posts.all()
        return Response({'message': 'Success', 'bookmarked_posts': PostSerializer(posts, many=True).data}, status=status.HTTP_200_OK)
    return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
def create_mass_users(request):
    last_names = ['Trần', 'Lê', 'Bùi', 'Hoàng', 'Nguyễn', 'Phạm', 'Võ', 'Đỗ', 'Phan', 'Đặng', 'Trịnh', 'Mai']
    first_names = ['Anh','Long', 'Dương', 'Hà', 'Huỳnh', 'Kim', 'Lâm', 'Lăng', 'Mai', 'Vương', 'Đăng', 'Khoa', 'Ngọc', 'Minh', 'Phương', 'Việt', 'Tú', 'Hoa', 'Sơn']

    for i in range(100):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        profile_name = convert_vn_to_eng(first_name).lower() + convert_vn_to_eng(last_name).lower() + str(random.randrange(21, 111))
        email = profile_name + '@gmail.com'
        gender = random.choice(['Male', 'Female'])
        date_of_birth = (timezone.now() - timezone.timedelta(days = random.randint(6570, 10950)))

        user = MyUser.objects.create(email=email,first_name=first_name,
        last_name=last_name,gender=gender.capitalize(),profile_name=profile_name, date_of_birth=date_of_birth)
        user.set_password(profile_name)
        user.save()

        UserAvatar.objects.create(user = user, image = 'avatar/' + str(random.randint(1, 4)) + random.choice(['.jpg', '.png']))

    return JsonResponse(last_names, safe=False)

@api_view(['GET'])
def create_random_connections(request):
    users = MyUser.objects.all()
    users_and_probs = []
    for user in users:
        following_probability = random.randint(6, 45)
        users_and_probs.append([user, following_probability])
    for user in users:
        for other_user in users_and_probs:
            if other_user[0] != user and other_user[0] not in user.followings.all():
                rand = random.randint(1, other_user[1])
                if rand == 1:
                    user.followings.add(other_user[0])
                    
    return JsonResponse([], safe=False)

@api_view(['GET'])
def create_random_interactions(request):
    users = MyUser.objects.all()
    gen = DocumentGenerator()
    for user in users:
        create_post_probs = random.randint(1, 15)
        if create_post_probs == 1:
            text_content = gen.paragraph()
            Post.objects.create(user = user, text_content = text_content)

    for user in users:
        for person in user.followings.all():
            person_posts = Post.objects.filter(user = person)
            for post in person_posts:
                like_post_probs = random.randint(1, 12)
                if like_post_probs == 1:
                    post.liked_by.add(user)

                comment_post_probs = random.randint(1, 17)
                if comment_post_probs == 1:
                    Comment.objects.create(post = post, user = user, content = gen.sentence())

    return JsonResponse([], safe=False)

@api_view(['GET'])
def network_analysis(request):
    profile_name = request.GET.get('profile_name', '')

    if profile_name == '':
        profile_name = None

    users = MyUser.objects.all()

    print(users)

    pair_list = []
    avatar = None
    for user in users:
        followings = user.followings.all()
        for person in followings:
            pair = [user.profile_name, person.profile_name]
            print(pair)
            pair_list.append(pair)

    g = nx.DiGraph()
    
    g.add_edges_from(pair_list)

    for user in users:
        if user.profile_name not in g.nodes():
            g.add_node(user.profile_name)
    
    i_d = nx.in_degree_centrality(g)
    o_d = nx.out_degree_centrality(g)
    b = nx.betweenness_centrality(g)
    c = nx.closeness_centrality(g)
    e = nx.eigenvector_centrality(g, max_iter=1000)
    cc = nx.clustering(g)

    draw_graph(g.copy(), nx.spring_layout(g, k=0.55), i_d, 'In Degree Centrality', profile_name)
    draw_graph(g.copy(), nx.spring_layout(g, k=0.55), o_d, 'Out Degree Centrality', profile_name)
    draw_graph(g.copy(), nx.spring_layout(g, k=0.55), b, 'Betweenness Centrality', profile_name)
    draw_graph(g.copy(), nx.spring_layout(g, k=0.55), c, 'Closeness Centrality', profile_name)
    draw_graph(g.copy(), nx.spring_layout(g, k=0.55), e, 'Eigenvector Centrality', profile_name)

    draw_network(g.copy(), nx.spring_layout(g, k=0.55))

    if profile_name is None:
        result = [i_d, o_d, b, c, e, cc]
    else:
        result = [i_d.get(profile_name, ''), o_d.get(profile_name, ''), b.get(profile_name, ''), c.get(profile_name, ''), e.get(profile_name, ''), cc.get(profile_name, '')]

    return JsonResponse(result, safe=False)
    
@api_view(['GET'])
def following_recommendation(request):
    profile_name = request.GET.get('profile_name', '')
    user = MyUser.objects.filter(profile_name = profile_name)
    if len(user) == 0:
        return JsonResponse([], safe=False)
    else:
        user = user[0]

    circle_profile_names = [profile_name]
    user_circle_pairs = []

    for person in user.followings.all():
        if person.profile_name not in circle_profile_names:
            circle_profile_names.append(person.profile_name)
        for person_2 in person.followings.all():
            if person_2.profile_name not in circle_profile_names:
                circle_profile_names.append(person_2.profile_name)

    print(circle_profile_names)
    
    users = MyUser.objects.filter(profile_name__in = circle_profile_names)

    # 0.1*like + 0.25*cmt + 0.5*(Ratio * FA / FB)
    for person in users:
        for person_2 in person.followings.all():
            if person_2 not in users:
                continue
            weight = 1
            person_2_posts = Post.objects.filter(user = person_2)
            for post in person_2_posts:
                if person in post.liked_by.all():
                    weight = weight + 0.1
                for comment in post.comments.all():
                    if comment.user == person:
                        weight = weight + 0.25

            FA = len(person.followers.all())
            FB = len(person_2.followers.all())
            FollowingsA = len(person.followings.all())
            if FB == 0:
                FB = 1
            if FA == 0:
                FA = 1
            if FollowingsA == 0:
                FollowingsA = 1
            FtFRatio = FA / FollowingsA
            weight = weight + (0.5 * (FtFRatio * FA / FB))

            user_circle_pairs.append([person.profile_name, person_2.profile_name, weight])

    g = nx.DiGraph()
    
    g.add_weighted_edges_from(user_circle_pairs)

    personalization = {}
    for node in g.nodes():
        if node != profile_name:
            personalization[node] = 0
        else:
            personalization[node] = 1

    print(personalization)
    # personalization={profile_name: 1}
    
    ppr = nx.pagerank(g, personalization=personalization, max_iter=150, tol=1e-10)
    ppr = sorted(ppr.items(), key=operator.itemgetter(1), reverse=True)

    recommendation_list = []

    for item in ppr.copy():
        followings = user.followings.all()
        target = followings.filter(profile_name = item[0])
        if len(target) == 0 and profile_name != item[0]:
            continue
        else:
            ppr.remove(item)
        
    for item in ppr.copy()[0:5]:
        target = MyUser.objects.filter(profile_name = item[0])[0]
        recommendation_list.append(UserSerializer(target).data)
    
    # recommendation_users = MyUser.objects.filter(profile_name__in = recommendation_list)

    print(ppr)

    draw_network(g.copy(), nx.spring_layout(g, k=0.9), {profile_name, ppr[0][0], ppr[1][0], ppr[2][0], ppr[3][0], ppr[4][0]})

    return JsonResponse(recommendation_list, safe=False, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def clear_db_data(request):
    # HashTag.objects.all().delete()
    # MyUser.objects.all().delete()
    # Post.objects.all().delete()
    # Comment.objects.all().delete()

    # x = [('A', 'B'), ('A', 'C'), ('A', 'D'), ('B', 'E'), ('C', 'F'), ('D', 'G'), ('C', 'H'), ('F', 'D'), ('E', 'A'), ('H', 'E')]
    # g = nx.DiGraph()
    # g.add_edges_from(x)
    # draw_network(g.copy(), nx.circular_layout(g), g.nodes())

    return JsonResponse([], safe=False)
