-- CreateTable
CREATE TABLE "car_parks" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "name_zh" TEXT,
    "address" TEXT,
    "address_zh" TEXT,
    "total_spaces" INTEGER NOT NULL,
    "available_spaces" INTEGER NOT NULL,
    "latitude" DOUBLE PRECISION,
    "longitude" DOUBLE PRECISION,
    "last_updated" TIMESTAMP(3) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "car_parks_pkey" PRIMARY KEY ("id")
);
