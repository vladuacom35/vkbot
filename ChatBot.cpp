﻿#include <map>
#include <cmath>
#include <algorithm>
#include <fstream>
#include <ctime>
#include <memory>
#include "ChatBot.h"

struct userinfo
{
    int smiles;
    int lastReply;
};

vector<wstring> request, noans;
vector<shared_ptr<vector<wstring> > > reply;
vector<vector<long long> > tf;
vector<pair<long long, long long> > fixedstem;
vector<pair<long long, long long> > replaced;
vector<long long> blacklist;
vector<double> tfnorm;
map<long long, int> df;
map<int, userinfo> users;
set<long long> names;

//wofstream misslog;
//wofstream alllog;

inline double tfidf(long long &word)
{
    return df.count(word) ? log((double)tf.size() / df[word]) : 0.;
}

inline double sqr(double x)
{
    return x * x;
}

double norm(vector<long long> &arr)
{
    double ans = 0;
    for(auto&& i: arr)
    {
        ans += sqr(tfidf(i));
    }
    return sqrt(ans);
}

wstring RandReply(vector<wstring> &v)
{
    return v.size() == 1 ? v[0] : v[rand() % v.size()];
}

int randint(int a, int b)
{
    return rand() % (b - a + 1) + a;
}

void SwapFirst(vector<wstring> &v, bool canStay)
{
    if(v.size() > 1)
    {
        swap(v[0], v[randint(1 - canStay, v.size()-1)]);
    }
}

long long phnamec = phash(L"firstnamec");

wstring BestReply(wstring &line, int id, bool conf)
{
    line += L' ';
    if(id >= 0 && users[id].lastReply && reply[abs(users[id].lastReply) - 1]->size() == 1 && line == L' ' + (*reply[abs(users[id].lastReply) - 1])[0] + L' ')
    {
        wcerr << line << L" - my reply\n";
        return L"";
    }
    vector<long long> words = splitWords(line, fixedstem, replaced, names);
    if(conf)
    {
        replace(words.begin(), words.end(), phname, phnamec);
    }
    sort(words.begin(), words.end());
    words.resize(unique(words.begin(), words.end()) - words.begin());
    for(long long &i : blacklist)
    {
        if(find(words.begin(), words.end(), i) != words.end())
        {
            wcerr << line << L" - blacklisted\n";
            return id >= 0 ? L"" : L"\\blacklisted";
        }
    }
    double mx = 0;
    int imx = 0;
    vector<long long> common;
    for(int i=0;i<(int)tf.size();i++)
    {
        common.clear();
        set_intersection(words.begin(), words.end(), tf[i].begin(), tf[i].end(), back_inserter(common));
        double ans = 0;
        for(auto&& word: common)
        {
            ans += sqr(tfidf(word));
        }
        ans /= tfnorm[i];
        if(ans > mx + 0.00000001)
        {
            mx = ans;
            imx = i;
        }
    }
    if(mx == 0)
    {
        wcerr << line << L" - no match\n";
        while(line.length() && line[0] == L' ')
        {
            line = line.substr(1);
        }
       /* if(id >= 0 && words.size())
        {
            misslog << line << endl;
            misslog.flush();
        }*/
        if(id >= 0 && users[id].smiles >= 2)
        {
            wcerr << "Too many smiles\n";
            return L"";
        }
        users[id].smiles++;
        return conf ? L"" : RandReply(noans);
    }
    wcerr << line << L" == " << request[imx] << L" (" << mx / norm(words) << L")";
    if(reply[imx]->size() > 1)
    {
        wcerr << L", " << reply[imx]->size() << L" replies";
    }
    wcerr << L'\n';
    if(users[id].lastReply == imx + 1)
    {
        users[id].lastReply = -(imx + 1);
    }
    else if(id >= 0 && users[id].lastReply == -(imx + 1))
    {
        wcerr << "Repeated\n";
        return L"";
    }
    else
    {
        users[id].lastReply = imx + 1;
    }
    users[id].smiles = 0;
    wstring ans = (*reply[imx])[0];
    SwapFirst(*reply[imx], 0);
   // alllog << line << L"\n==" << request[imx] << L'\n' << ans << endl;
   // alllog.flush();
    return ans;
}

wstring Say(wstring &curline, int id, bool conf)
{
    return BestReply(curline, id, conf);
}

vector<wstring> splitReply(const wstring &t)
{
    vector<wstring> ans;
    wstring s;
    for(wchar_t i : t)
    {
        if(i == L'|')
        {
            if(s.length())
                ans.push_back(s);
            s.clear();
        }
        else
        {
            s.push_back(i);
        }
    }
    if(s.length())
        ans.push_back(s);
    SwapFirst(ans, 1);
    return ans;
}

void AddReply(const wstring &req, const wstring &rep)
{
    shared_ptr<vector<wstring> > v(new vector<wstring>());
    *v = splitReply(rep);
    for(wstring& i : splitReply(req))
    {
        reply.push_back(v);
        request.push_back(i);
        vector<long long> words = splitWords(i, fixedstem, replaced, names);
        sort(words.begin(), words.end());
        words.resize(unique(words.begin(), words.end()) - words.begin());
        for(auto& j: words)
        {
            df[j]++;
        }
        tf.push_back(words);
    }
}

wchar_t buf1[12000], buf2[12000];
const string file = "bot.txt";
const string filena = "noans.txt";
const string filebl = "blacklist.txt";
const string filestem = "fixedstem.txt";
const string filenames = "names.txt";

void Load()
{
    locale loc("");
    //misslog.close();
    //misslog.open("miss.log", ofstream::out | ofstream::app);
    //misslog.imbue(loc);
    //alllog.close();
    //alllog.open("all.log", ofstream::out | ofstream::app);
    //alllog.imbue(loc);
    reply.clear();
    request.clear();
    tf.clear();
    tfnorm.clear();
    df.clear();
    noans.clear();
    blacklist.clear();
    fixedstem.clear();
    names.clear();
    srand(time(0));
    wifstream fin(file);
    wifstream fstem(filestem);
    fstem.imbue(loc);
    while(fstem >> buf1)
    {
        fstem >> buf2;
        if(buf1[0] == '$')
        {
            replaced.push_back(make_pair(stem(buf1 + 1), stem(buf2)));
        }
        else
        {
            wstring s = buf1;
            for(auto &i : s)
                i = towupper(i);
            fixedstem.push_back(make_pair(phash(s), phash(buf2)));
        //    wcerr << s << endl;
        }
    }
    fstem.close();
    fin.imbue(loc);
    while(fin.getline(buf1, 10000))
    {
        fin.getline(buf2, 10000);
        AddReply(buf1, buf2);  //this should be done BEFORE filling names
    }
    df[phnamec] = 10000;
    for(auto&& i : tf)
    {
        tfnorm.push_back(norm(i));
    }
    fin.close();
    wifstream fna(filena);
    fna.imbue(loc);
    while(fna.getline(buf1, 10000))
    {
        noans.push_back(buf1);
    }
    wifstream fbl(filebl);
    fbl.imbue(loc);
    while(fbl.getline(buf1, 10000))
    {
        blacklist.push_back(phash(buf1));
    }
    fbl.close();
    wifstream fnm(filenames);
    fnm.imbue(loc);
    while(fnm.getline(buf1, 10000))
    {
        for(int i=0;buf1[i];i++)
        {
            buf1[i] = towupper(buf1[i]);
        }
        names.insert(phash(buf1));
    }
    fbl.close();
    for(auto &i : users)
    {
        i.second.lastReply = 0;
    }
}

