import os,time


a_list = ['git checkout fcg',
    'git pull',
    'git add .', 
    'git commit -m "fcg_commit"', 
    'git push -u origin fcg',
    'git checkout develop',
    'git pull',
    'git merge fcg',
    'git checkout fcg'
            ]
for i in a_list:
    print(i)
    os.system(i)
print('�ύ���')
input()