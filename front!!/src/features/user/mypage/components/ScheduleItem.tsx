import { useState } from 'react';

import { EditSchedule } from '@/features/user/mypage/components/handle-schedule/EditSchedule';

import { receivedSchedule } from '@/features/user/types';

const bgColor: { [key: string]: string } = {
  중요: 'bg-pink-400',
  행사: 'bg-sky-500',
  회의: 'bg-amber-600',
  일정: 'bg-green-700',
  완료: 'bg-gray-900',
};

export const ScheduleItem = ({
  date,
  title,
  category,
  id,
  description,
  email,
}: receivedSchedule) => {
  const [isOpen, setIsOpen] = useState(false);

  const openModal = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    setIsOpen(true);
  };
  const closeModal = () => {
    setIsOpen(false);
  };
  return (
    <>
      {isOpen && (
        <EditSchedule
          email={email}
          closeModal={closeModal}
          date={date}
          title={title}
          categoryName={category}
          id={id}
          description={description}
        />
      )}
      <button
        onClick={openModal}
        className={`${bgColor[category]} border text-stone-200 font-bold w-[95%] trucate self-center overflow-hidden mb-0.5`}>
        {title}
      </button>
    </>
  );
};
