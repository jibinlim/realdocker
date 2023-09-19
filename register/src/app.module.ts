import { Module } from '@nestjs/common';
import { AuthModule } from './auth/auth.module';
import { TypeOrmModule } from '@nestjs/typeorm';
import { User } from './auth/entity/user.entity';
import { TypeOrmExModule } from './db/typeorm-ex.module';
import { UserRepository } from './auth/user.repository';
import { ScheduleModule } from './schedule/schedule.module';
import { Schedule } from './schedule/entity/schedule.entity';
import { ScheduleRepository } from './schedule/schedule.repository';

@Module({
  imports: [
    TypeOrmModule.forRoot({
      type: 'mariadb',
      host: 'svc.sel5.cloudtype.app',
      port: 30039,
      username: 'root',
      password: '1234',
      database: 'plc',
      entities: [User, Schedule],
      autoLoadEntities: false,
      synchronize: true,
    }),
    TypeOrmExModule.forCustomRepository([UserRepository, ScheduleRepository]),
    AuthModule,
    ScheduleModule,
  ],
})
export class AppModule {}
