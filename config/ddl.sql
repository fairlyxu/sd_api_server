 create table SD_TASK
        (
            id           int unsigned auto_increment primary key,
            requestid    varchar(128)                              not null,
            create_time  datetime(3) default CURRENT_TIMESTAMP(3) not null,
            update_time  datetime(3) default CURRENT_TIMESTAMP(3) not null on update CURRENT_TIMESTAMP(3),
            delete_time  datetime(3)                              null,
            status       tinyint(1)  default 1                    null comment '-1=失败，0=正在处理，1=排队中，2=生成成功',
            image        varchar(1024)                              not null comment '输入图像',
            prompt       varchar(1024)                              null,
            a_prompt     varchar(1024)                              null,
            n_prompt     varchar(1024)                              null,
            res_img1     varchar(1024)                              null comment '输出图像',
            res_img2     varchar(1024)                              null comment '输出图像'
        )  collate = utf8mb4_general_ci;