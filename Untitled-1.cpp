#include<stdio.h>
#include<conio.h>
void main(){
     int a;
     int b;
     int c;
     
     printf("input number(1)");
     scanf("%s",a);
     
     printf("input number(2)");
     scanf("%s",b);
     
     printf("choose your operation \n1).Plus \n2).Minus \n3.)times \n4).Divine");
     scanf("%s",c);
     
     if(c==1){
              printf("%d",a+b);
     }else if(c==2){
           if(a>b){
                   printf("Cant  Subtrac");
           }else
                   printf("%d",a-b);
                   }            
     }else if(c==3){
           printf("%d",a*b);
           
     }else if(c==4){
           if(a>b){
                   printf("Cant Divine");
           }else(){
                   printf("%d",a/b);
                   }
           }