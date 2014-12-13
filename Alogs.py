import apachelog, sys
import pandas as pd
import numpy as np
from pandas import Series,  DataFrame, Panel
from pylab import *
import pygeoip
#import mpl_toolkits.basemap #import basemap
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import matplotlib.cm as cm
from tabulate import tabulate  #pour organiser l'affichage dans un tableau
##################################################################################
#####################                                   ##########################
##################################################################################

#pour installer une module python via pip install pandas basemap numpy.

#Analyse des fichier logs des serveurs OVH pour la detection des anomalis
#Date : 16/11/2014

#creation du parser des lignes du fichier
fformat = r'%h %V %l %t \"%r\" %>s %b \"%i\" \"%{User-Agent}i\"'
p = apachelog.parser(fformat)

#Importer un fichier log
#log = open('b-techs.ma-13-11-2014.log')
log = open('b-techs.ma-10-2014.log')

###Definision des fonctions
##Fonction pour affichage en mode tableau
def tableViews(data, headrs = []):
       print tabulate(data, headrs, tablefmt="grid")       

###Stockage des resultat dans un fichier#####
def SaveInFile(data, fileName):
       fichier = open(fileName,"w")
       fichier.write(data)
       fichier.close()

#test avec l'analyse d'une seul ligne de loge du serveur OVH
sample_string ='94.23.251.171 b-techs.org - [13/Nov/2014:08:45:17 +0100] "GET / HTTP/1.1" 403 202 "-" "Mozilla/5.0 (compatible; WASALive-Bot ; http://blog.wasalive.com/wasalive-bots/)"'

#declaration d'un tableau dynamique pour concerver les lignes#
log_list = []
for line in log:
       try:
              data = p.parse(line)
       except:
              sys.stderr.write("Unable to parse %s" % line)
       data['%t'] = data['%t'][1:12]+' '+data['%t'][13:21]+' '+data['%t'][22:27]              
       log_list.append(data)

df = DataFrame(log_list)
print tableViews(df[0:40])
#SaveInFile(df[0:40], "b-techs.ma-10-2014.txt")

#nous allons suprimer quelque donner que nous n'allons pas utiliser.

del df['%V'];
del df['%i'];
del df['%l'];
del df['%{User-Agent}i']

#nous allons renomer les colonne que nous afichons.

df = df.rename(columns={'%>s': 'Status', '%b':'b', '%h':'IP', '%r':'Request', '%t': 'Time'})
#print df.head()
#cette ligne permet de concertir le temps (datetime)
df.index = pd.to_datetime(df.pop('Time'))

#convertir le type status en int
df['Status'] = df['Status'].astype('int')
df['b'][93]

#df['b'] = df['b'].replace('-', 'NaN', regex=True).astype('float')
#df['b'] = df['b']/1048576.
#print df['b']
#df['b'][93]

def dash2nan(x):
       if x == '-':
              x = np.nan
       else:
              x = float(x) * 10**(-3) #Convertir les byts en K-byts multipier 0.0001
       return x

df['b'] = df['b'].apply(dash2nan).astype('float')

#print df['b']
#df['b'].plot()
#df_s = df['b'].resample('5t', how='count')
#df_s.plot(color='r')
#show()

df_b = df['b'].resample('10t', how=['count','sum'])
#df_b['count'].plot(color='r')
#df_b['sum'].plot(color = 'g')
#legend()
#df_b['sum'].plot(secondary_y = True)
#show()

#print tabulate( df_b.corr(), tablefmt="grid")

#tableViews(df_b.corr(), ["count","sum"])



print '#########################################################"'
#cc = df[df['b']<0.3]
#print cc
#cc.b.hist(bins=200)
cc = df[(df['b']>0.220)&(df['b']<0.3)]
#cc.b.hist(bins=100)
#print cc.head()

#########Code pour definir la statur de notre serveur pour le mois 10/2014###########
t_span = '2H'
df_404 = df['Status'][df['Status'] == 404].resample(t_span, how='count')
df_403 = df['Status'][df['Status'] == 403].resample(t_span, how='count')
df_301 = df['Status'][df['Status'] == 301].resample(t_span, how='count')
df_304 = df['Status'][df['Status'] == 304].resample(t_span, how='count')
df_200 = df['Status'][df['Status'] == 200].resample(t_span, how='count')

status_df = DataFrame({'Not Found' : df_404, 'Forbidden':df_403, 'Moved Permanently':df_301, 'Not Modified':df_304, 'OK':df_200,})

#print tabulate(status_df.head(),headers=["404","403","301","304","200"], tablefmt="grid")

#status_df.plot(figsize=(10, 3))
#status_df[['Not Found','Forbidden','Moved Permanently','Not Modified']].plot(kind='barh', stacked=True, figsize=(10, 7))

#Plotage des status du serveur 
grouped_status = df.groupby('Status')
grouped_status.head(2)
#grouped_status.size().plot(kind='bar')
#legend()

#plotage des tatut 200, 301 c'est possible de les faires avec les autre status de serveur
t_span = '30t'
'''grouped_status.get_group(301)['Status'].resample(t_span, how='count').plot(color='g', label='301')
legend()
grouped_status.get_group(200)['Status'].resample(t_span, how='count').plot(color='b', secondary_y=True, label='200')
'''
#####Calcule des adress IP ####
ips = df.groupby('IP').size()
ips.sort()
#ips[-20:].plot(kind='barh') #visualisation des Ip dans un plot

#Visualisation des ip dans un tableau les top 10 adress IP.
ips_fd = DataFrame({'Number of requests' : ips[-10:]})
ips_fd = ips_fd.sort(columns='Number of requests', ascending=False)
#print tabulate (ips_fd , headers=["IP adress","Number Request"], tablefmt='grid')

##Regroupement des adress IP et des status####
ips_status = df.groupby(['IP', 'Status']).size()
ips_status.sort()
#ips_status[-20:].plot(kind='barh')

####Imformation geographique#####
gi = pygeoip.GeoIP('./GeoLiteCity.dat', pygeoip.MEMORY_CACHE)
ipcon = gi.record_by_addr('192.99.149.88')

####Afficher les infos concernat une adresse IP dans une cituation geographic####
#print ipcon

ipcon = []
for iip in ips.index:
       rres = gi.record_by_addr(iip)
       rres['Number'] = ips[iip]
       #delete some fields we don't need
       del rres['area_code']
       del rres['dma_code']
       del rres['metro_code']
       del rres['postal_code']
       #del rres['region_name']
       del rres['time_zone']
       del rres['country_code']
       ipcon.append(rres)

reg = DataFrame(ipcon, index = ips.index)
#print tabulate(reg, headers=["Number","city","continent","country_code3","country_name","latitude","longitude","region_name"], tablefmt="grid")

#regroupement des connexion par pays
'''country = reg.groupby('country_code3')
ff = country.Number.agg('sum').copy()
ff.sort()
ff[-15:].plot(kind='barh')
show()'''
#Regroupement par ville
'''city = reg.groupby('city')
ff = city.Number.agg('sum').copy()
ff.sort()
ff[-25:].plot(kind='barh')'''

def gmet(X):
       X = X.split()
       return X[0]

df['Method'] = df.Request.apply(gmet)

met = df.groupby(['Method','IP']).size()

#print met.head()


post = met['POST'].copy()
#post.sort()
'''get = met['GET'].copy()
get.sort()
'''
#post[-10:].plot(kind='barh')
#get[-15:].plot(kind='barh')


#post[-5:]

win = df[df.IP == '146.185.239.52'][0:5]
print tabulate(win,headers=["Request","b","IP","fichier","Method"] ,tablefmt='grid')

###Representation geographic des donnes###
#visualisation dans un Map du monde entier##
'''m = Basemap(projection='robin',lon_0=0,resolution='c')
x, y = m(reg['longitude'].values,reg['latitude'].values)

figure(figsize=(15,15))
m.drawcoastlines(linewidth=0.25)
m.drawcountries(linewidth=0.25)
m.fillcontinents(color='coral',lake_color='aqua')
m.drawmapboundary(fill_color='white')
m.drawmeridians(np.arange(0,360,30))
m.drawparallels(np.arange(-90,90,30))
m.scatter(x,y,s=reg['Number']*3,c=reg['Number']/5,marker='o',zorder=4, cmap=cm.Paired,alpha=0.5)
#show()
'''
##Visualisation des donnees par continant###
'''m = Basemap(projection='cyl',llcrnrlat=35,urcrnrlat=80,llcrnrlon=-10,urcrnrlon=50,resolution='l')
x, y = m(reg['longitude'].values,reg['latitude'].values)

figure(figsize=(15,15))
m.drawcoastlines(linewidth=0.25)
m.drawcountries(linewidth=0.25)
m.fillcontinents(color='white',lake_color='aqua')
m.drawmapboundary(fill_color='aqua')
m.drawmeridians(np.arange(0,360,30))
m.drawparallels(np.arange(-90,90,30))
m.scatter(x,y,s=reg['Number']*50,c=reg['Number'],marker='O',zorder=4, cmap=cm.gist_ncar ,alpha=0.2)
#show()
'''