#!/bin/bash
# Quick fix for academic section layout
sed -i '' '107,130d' /Users/dszab22/Documents/Development/mindfort/templates/index_public.html
sed -i '' '106 a\
                    <div class="text-center w-full mb-6">\
                        <p class="text-[8px] font-bold text-gray-400 uppercase tracking-[0.25em] opacity-60">Academic Institutions & Funding Acknowledgments</p>\
                    </div>\
                    \
                    <div class="flex flex-col md:flex-row gap-8 w-full items-start">\
                        <!-- Left: Funding text (60%) -->\
                        <div class="w-full md:w-3/5">\
                            <p class="text-[9px] text-gray-400 leading-relaxed font-normal opacity-70">\
                                This research is partly funded by the Strategic Research Council (SRC), established within the Research Council of Finland (Grants 356128, 335625, 335729), and Research Fellowship funding by the Research Council of Finland (Grants 356128, 349637 and 353790). The research was also partly supported by JSPS Bilateral Collaboration between Japan and Finland (Grant Number: JPJSBP120232701). This work was partly supported by JST ASPIRE for Top Scientists (Grant Number JPMJAP2405).\
                            </p>\
                        </div>\
                        \
                        <!-- Right: Logos (40%) -->\
                        <div class="w-full md:w-2/5 flex flex-col items-center gap-4">\
                            <div class="flex flex-wrap justify-center items-center gap-6 grayscale opacity-40 hover:grayscale-0 hover:opacity-100 transition-all duration-700">\
                                <div class="p-1.5 border border-blue-50 rounded-lg bg-gray-50/30">\
                                    <img src="{{ url_for('"'"'static'"'"', filename='"'"'img/oulu_logo.png'"'"') }}" alt="University of Oulu" class="h-10 object-contain">\
                                </div>\
                                <div class="p-1.5 border border-blue-50 rounded-lg bg-gray-50/30">\
                                    <img src="{{ url_for('"'"'static'"'"', filename='"'"'img/utokyo_logo.png'"'"') }}" alt="The University of Tokyo" class="h-10 object-contain">\
                                </div>\
                            </div>\
                            <p class="text-[11px] text-gray-500 font-bold uppercase tracking-wider text-center">\
                                University of Oulu &bull; The University of Tokyo\
                            </p>\
                            <p class="text-[10px] text-gray-400 font-medium italic text-center">\
                                Created at the University of Oulu in collaboration with The University of Tokyo\
                            </p>\
                        </div>\
                    </div>
'  /Users/dszab22/Documents/Development/mindfort/templates/index_public.html
