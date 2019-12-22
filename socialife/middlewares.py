import json

import re
import sys

import networkx as nx
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.image as mpimg

from io import BytesIO
import base64

from django.core.files.base import ContentFile
from .models import UserAvatar
from .models import MyUser, NetworkVisualization

def check_user_with_token(request):
    user_email = request.user.email
    data = json.loads(request.body.decode('utf-8'))
    request_email = data['email']
    if user_email == request_email:
        return True
    else:
        return False


patterns = {
    '[àáảãạăắằẵặẳâầấậẫẩ]': 'a',
    '[đ]': 'd',
    '[èéẻẽẹêềếểễệ]': 'e',
    '[ìíỉĩị]': 'i',
    '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
    '[ùúủũụưừứửữự]': 'u',
    '[ỳýỷỹỵ]': 'y'
}

def convert_vn_to_eng(text):
    """
    Convert from 'Tieng Viet co dau' thanh 'Tieng Viet khong dau'
    text: input string to be converted
    Return: string converted
    """
    output = text
    for regex, replace in patterns.items():
        output = re.sub(regex, replace, output)
        # deal with upper case
        output = re.sub(regex.upper(), replace.upper(), output)
    return output

plt.rcParams['figure.dpi'] = 900
def draw_network(G, pos, node_labels = None):
    options = {
        'node_size': 150,
        'width': 0.3,
        'arrowsize': 6,
        'edgecolors': 'black',
        'linewidths': 0.7,
    }

    plt.title('Network Visualization')
    plt.axis('off')

    if node_labels is not None:
        labels = {}
        for node in G.nodes():
            if node in node_labels:
                labels[node] = node
        nx.draw_networkx_labels(G, pos=pos, labels=labels, font_size=6, font_color='black')
    
    nx.draw(G, pos=pos, **options)

    f = BytesIO()
    plt.savefig(f)
    content_file = ContentFile(f.getvalue())
    model_object = NetworkVisualization.objects.all()

    if len(model_object) == 0:
        model_object = NetworkVisualization.objects.create()
    else:
        model_object = model_object[0]

    model_object.visualization.delete()
    model_object.visualization.save('Visualization' + '.png', content_file)
    model_object.save()
    plt.close()

def draw_graph(G, pos, measures, measure_name, node_label=None):
    nodes = nx.draw_networkx_nodes(G, pos, cmap=plt.cm.plasma, 
                                node_color=list(measures.values()),
                                nodelist=measures.keys(), node_size = 180, edgecolors='black', linewidths=0.7)

    # reversed_measures = {k: k for k, v in measures.items()}
    # labels = nx.draw_networkx_labels(G, pos, labels=reversed_measures, font_size = 3)

    edges = nx.draw_networkx_edges(G, pos, width=0.3, arrowsize=7)
    # edge_labels = nx.get_edge_attributes(G,'weight')
    # edge_labels=nx.draw_networkx_edge_labels(G ,pos, edge_labels, font_size=2)

    nodes.set_norm(mcolors.SymLogNorm(linthresh=0.01, linscale=1))

    if node_label is not None:
        labels = {}
        node_color = {}
        for node in G.nodes():
            if node == node_label:
                labels[node] = node
                node_color[node] = float(measures.get(node, ''))

        nx.draw_networkx_labels(G,pos,labels,font_size=8,font_color='black')

        label_nodes = nx.draw_networkx_nodes(G, pos, cmap=plt.cm.plasma, 
                        node_color=list(node_color.values()),
                        nodelist=labels, node_size = 320, edgecolors='black', linewidths=0.8)
        label_nodes.set_norm(mcolors.SymLogNorm(linthresh=0.01, linscale=1))

        for group in sorted(nx.connected_components(G.to_undirected())):
            if node_label in group:
                measures = {k:v for k,v in measures.items() if k in group}
                pairs_to_remove = []
                for pair in G.edges():
                    if pair[0] not in group or pair[1] not in group:
                        pairs_to_remove.append(pair)
                for pair in pairs_to_remove:
                    G.remove_edge(pair[0], pair[1])
                break

    plt.title(measure_name)
    plt.colorbar(nodes, shrink=0.6)
    plt.axis('off')

    f = BytesIO()
    plt.savefig(f)
    content_file = ContentFile(f.getvalue())

    if node_label is None:
        model_object = NetworkVisualization.objects.all()

        if len(model_object) == 0:
            model_object = NetworkVisualization.objects.create()
        else:
            model_object = model_object[0]

    else:
        model_object = MyUser.objects.filter(profile_name = node_label)
        if len(model_object) == 0: 
            return
        else: 
            model_object = model_object[0]

    if measure_name == 'In Degree Centrality':
        model_object.in_degree_centrality.delete()
        model_object.in_degree_centrality.save(measure_name + '.png', content_file)
    if measure_name == 'Out Degree Centrality':
        model_object.out_degree_centrality.delete()
        model_object.out_degree_centrality.save(measure_name + '.png', content_file)
    if measure_name == 'Betweenness Centrality':
        model_object.betweenness_centrality.delete()
        model_object.betweenness_centrality.save(measure_name + '.png', content_file)
    if measure_name == 'Closeness Centrality':
        model_object.closeness_centrality.delete()
        model_object.closeness_centrality.save(measure_name + '.png', content_file)
    if measure_name == 'Eigenvector Centrality':
        model_object.eigenvector_centrality.delete()
        model_object.eigenvector_centrality.save(measure_name + '.png', content_file)

    model_object.save()
    plt.close()